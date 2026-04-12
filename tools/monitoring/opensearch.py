"""
tools/monitoring/opensearch.py
───────────────────────────────
LangChain tools for querying OpenSearch logs.
Covers: error log search, recent logs, aggregation queries.
"""
from __future__ import annotations
from typing import Optional
import httpx
import structlog
from langchain_core.tools import tool
from config.settings import get_settings

logger = structlog.get_logger(__name__)


def _os_url() -> str:
    return str(get_settings().monitoring.opensearch_url).rstrip("/")

def _auth():
    s = get_settings().monitoring
    return (s.opensearch_username, s.opensearch_password)


@tool("search_error_logs")
async def search_error_logs(
    query: str,
    index: str = "openstack-*",
    time_range: str = "1h",
    max_results: int = 20,
) -> str:
    """
    Search OpenSearch for error or warning log entries.
    Use this to investigate incidents or find recent error patterns.
    Args:
        query: Search terms (e.g. 'nova compute error', instance UUID)
        index: Index pattern (default: openstack-*)
        time_range: How far back to look (e.g. '1h', '6h', '24h')
        max_results: Maximum log lines to return (default 20)
    """
    body = {
        "size": max_results,
        "sort": [{"@timestamp": {"order": "desc"}}],
        "query": {
            "bool": {
                "must": [
                    {"query_string": {"query": query}},
                    {"range": {"@timestamp": {"gte": f"now-{time_range}", "lte": "now"}}},
                ]
            }
        },
        "_source": ["@timestamp", "level", "message", "host", "service"],
    }

    try:
        async with httpx.AsyncClient(timeout=30, auth=_auth(), verify=False) as client:
            resp = await client.post(
                f"{_os_url()}/{index}/_search",
                json=body,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

        hits = data.get("hits", {}).get("hits", [])
        total = data.get("hits", {}).get("total", {}).get("value", 0)

        if not hits:
            return f"No log entries found for query: `{query}` in last {time_range}."

        lines = [f"**{total} log entries** found (showing {len(hits)}):\n"]
        for hit in hits:
            src = hit.get("_source", {})
            ts = src.get("@timestamp", "N/A")[:19]
            level = src.get("level", "INFO").upper()
            msg = src.get("message", "")[:200]
            host = src.get("host", "")
            lines.append(f"`{ts}` **[{level}]** `{host}` — {msg}")

        return "\n".join(lines)

    except Exception as exc:
        logger.error("opensearch_search_error", query=query, error=str(exc))
        return f"Error searching OpenSearch: {exc}"


@tool("get_service_error_count")
async def get_service_error_count(
    service: str,
    time_range: str = "1h",
) -> str:
    """
    Get the count of ERROR-level log entries per OpenStack service over a time window.
    Useful for quickly identifying which service is having problems.
    Args:
        service: OpenStack service name (e.g. 'nova', 'neutron', 'cinder', or 'all')
        time_range: Time window (e.g. '1h', '6h', '24h')
    """
    query_filter = f"service:{service} AND" if service != "all" else ""
    body = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {"query_string": {"query": f"{query_filter} level:ERROR"}},
                    {"range": {"@timestamp": {"gte": f"now-{time_range}", "lte": "now"}}},
                ]
            }
        },
        "aggs": {
            "by_service": {
                "terms": {"field": "service.keyword", "size": 20}
            }
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30, auth=_auth(), verify=False) as client:
            resp = await client.post(
                f"{_os_url()}/openstack-*/_search",
                json=body,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

        buckets = data.get("aggregations", {}).get("by_service", {}).get("buckets", [])
        total = data.get("hits", {}).get("total", {}).get("value", 0)

        if not buckets:
            return f"✅ No ERROR logs for {service} in the last {time_range}."

        lines = [f"**Error counts by service (last {time_range}) — Total: {total}**\n"]
        for b in buckets:
            bar = "█" * min(b["doc_count"] // 10, 30)
            lines.append(f"- **{b['key']}**: {b['doc_count']} errors  {bar}")

        return "\n".join(lines)

    except Exception as exc:
        logger.error("opensearch_error_count_error", service=service, error=str(exc))
        return f"Error querying OpenSearch: {exc}"


OPENSEARCH_TOOLS = [search_error_logs, get_service_error_count]
