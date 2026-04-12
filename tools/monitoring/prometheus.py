"""
tools/monitoring/prometheus.py
───────────────────────────────
LangChain tools for querying Prometheus metrics.

Covers: instant queries, range queries, and alert status.
"""
from __future__ import annotations

import time
from typing import Optional

import httpx
import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from config.settings import get_settings

logger = structlog.get_logger(__name__)


def _prom_url() -> str:
    return str(get_settings().monitoring.prometheus_url).rstrip("/")


# ── Input schemas ────────────────────────────────────────────────────────────

class PromQLInput(BaseModel):
    query: str = Field(..., description="Valid PromQL expression, e.g. 'node_cpu_seconds_total'")
    step: str = Field("60s", description="Resolution step for range queries (e.g. '60s', '5m')")
    duration: str = Field("1h", description="Look-back window (e.g. '1h', '30m', '24h')")


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool("query_metric", args_schema=PromQLInput)
async def query_metric(query: str, step: str = "60s", duration: str = "1h") -> str:
    """
    Execute a PromQL instant query against Prometheus.
    Use this to get the current value of any metric.
    Examples: node_memory_MemAvailable_bytes, up{job='nova-compute'}
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{_prom_url()}/api/v1/query",
                params={"query": query},
            )
            resp.raise_for_status()
            data = resp.json()

        if data["status"] != "success":
            return f"Prometheus query failed: {data.get('error', 'unknown')}"

        results = data["data"]["result"]
        if not results:
            return f"No data returned for query: `{query}`"

        lines = [f"**Metric:** `{query}`\n"]
        for r in results[:20]:  # cap output
            labels = ", ".join(f"{k}={v}" for k, v in r["metric"].items() if k != "__name__")
            value = r["value"][1]
            lines.append(f"- {labels or '(no labels)'}: **{value}**")

        if len(results) > 20:
            lines.append(f"\n_…and {len(results) - 20} more results._")

        return "\n".join(lines)

    except Exception as exc:
        logger.error("prometheus_query_error", query=query, error=str(exc))
        return f"Error querying Prometheus: {exc}"


@tool("query_metric_range", args_schema=PromQLInput)
async def query_metric_range(query: str, step: str = "60s", duration: str = "1h") -> str:
    """
    Execute a PromQL range query against Prometheus.
    Use this to get time-series data for trend analysis.
    Returns min/max/avg summary statistics over the window.
    """
    try:
        end = int(time.time())
        # Parse duration string to seconds
        duration_map = {"m": 60, "h": 3600, "d": 86400}
        unit = duration[-1]
        amount = int(duration[:-1])
        seconds = amount * duration_map.get(unit, 60)
        start = end - seconds

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{_prom_url()}/api/v1/query_range",
                params={"query": query, "start": start, "end": end, "step": step},
            )
            resp.raise_for_status()
            data = resp.json()

        if data["status"] != "success":
            return f"Prometheus range query failed: {data.get('error', 'unknown')}"

        results = data["data"]["result"]
        if not results:
            return f"No time-series data for: `{query}` over last {duration}."

        lines = [f"**Range query:** `{query}` (last {duration})\n"]
        for r in results[:10]:
            labels = ", ".join(f"{k}={v}" for k, v in r["metric"].items() if k != "__name__")
            values = [float(v[1]) for v in r["values"]]
            if values:
                mn, mx, avg = min(values), max(values), sum(values) / len(values)
                lines.append(f"- {labels or 'default'}: min={mn:.2f}, max={mx:.2f}, avg={avg:.2f}")

        return "\n".join(lines)

    except Exception as exc:
        logger.error("prometheus_range_error", query=query, error=str(exc))
        return f"Error querying Prometheus range: {exc}"


@tool("get_firing_alerts")
async def get_firing_alerts() -> str:
    """
    Retrieve all currently firing alerts from Prometheus Alertmanager.
    Use this first when investigating incidents or checking system health.
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{_prom_url()}/api/v1/alerts")
            resp.raise_for_status()
            data = resp.json()

        alerts = data.get("data", {}).get("alerts", [])
        firing = [a for a in alerts if a.get("state") == "firing"]

        if not firing:
            return "✅ No alerts are currently firing."

        lines = [f"🔥 **{len(firing)} alert(s) firing:**\n"]
        for a in firing:
            name = a.get("labels", {}).get("alertname", "Unknown")
            severity = a.get("labels", {}).get("severity", "unknown")
            summary = a.get("annotations", {}).get("summary", "No summary")
            instance = a.get("labels", {}).get("instance", "")
            lines.append(f"- **{name}** [{severity.upper()}] — {summary} `{instance}`")

        return "\n".join(lines)

    except Exception as exc:
        logger.error("prometheus_alerts_error", error=str(exc))
        return f"Error fetching alerts: {exc}"


@tool("get_instance_metrics")
async def get_instance_metrics(instance_id: str) -> str:
    """
    Get CPU, memory, network, and disk metrics for a specific OpenStack instance.
    Provide the OpenStack instance UUID.
    """
    queries = {
        "CPU usage (%)": f'100 - avg(rate(node_cpu_seconds_total{{mode="idle", instance=~"{instance_id}.*"}}[5m])) * 100',
        "Memory available (GB)": f'node_memory_MemAvailable_bytes{{instance=~"{instance_id}.*"}} / 1e9',
        "Network in (MB/s)": f'rate(node_network_receive_bytes_total{{instance=~"{instance_id}.*"}}[5m]) / 1e6',
        "Network out (MB/s)": f'rate(node_network_transmit_bytes_total{{instance=~"{instance_id}.*"}}[5m]) / 1e6',
        "Disk read (MB/s)": f'rate(node_disk_read_bytes_total{{instance=~"{instance_id}.*"}}[5m]) / 1e6',
    }

    lines = [f"**Metrics for instance: {instance_id}**\n"]
    async with httpx.AsyncClient(timeout=30) as client:
        for label, query in queries.items():
            try:
                resp = await client.get(
                    f"{_prom_url()}/api/v1/query", params={"query": query}
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("data", {}).get("result", [])
                if results:
                    value = float(results[0]["value"][1])
                    lines.append(f"- {label}: **{value:.2f}**")
                else:
                    lines.append(f"- {label}: N/A")
            except Exception as exc:
                lines.append(f"- {label}: Error ({exc})")

    return "\n".join(lines)


# ── Tool registry ─────────────────────────────────────────────────────────────

PROMETHEUS_TOOLS = [
    query_metric,
    query_metric_range,
    get_firing_alerts,
    get_instance_metrics,
]
