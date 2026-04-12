"""
agents/monitoring/agent.py
──────────────────────────
Monitoring & Actions Agent

Responsibilities:
  - Poll Prometheus for anomalies and threshold breaches
  - Parse OpenSearch alerts and error patterns
  - Trigger automated remediation for known failure modes
  - Escalate to RCA agent for complex incidents
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog
from langchain_core.messages import AIMessage, ToolMessage

from agents.base import AgentResult, BaseAgent
from tools.monitoring.prometheus import PROMETHEUS_TOOLS
from tools.openstack.nova import NOVA_TOOLS

logger = structlog.get_logger(__name__)

MONITORING_SYSTEM_PROMPT = """You are an OpenStack monitoring engineer responsible for
real-time system health and automated incident response.

## Responsibilities
- Check all firing Prometheus alerts
- Identify anomalies: CPU > 90%, memory pressure, disk filling up, instance errors
- For known issues, apply automatic remediation (e.g. restart a hung service)
- For unknown issues, produce a clear incident summary for escalation to the RCA agent
- Track metrics trends over time (last 1h, 6h, 24h)

## Response format
Always begin with a **Health Summary** (🟢 Healthy / 🟡 Warning / 🔴 Critical)
then list specific findings, then recommended actions.

## Auto-remediation rules (execute immediately, no approval needed)
- Instance stuck in BUILD > 20min → soft reboot
- Instance in ERROR state → get console log, report

## Actions requiring approval
- Hard reboot, delete, or resize any instance
- Any action affecting more than 3 resources
"""


class MonitoringAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "MonitoringAgent"

    @property
    def system_prompt(self) -> str:
        return MONITORING_SYSTEM_PROMPT

    @property
    def tools(self):
        return PROMETHEUS_TOOLS + NOVA_TOOLS

    async def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> AgentResult:
        self._log.info("monitoring_agent_run", task_preview=task[:80])

        llm_with_tools = self._bind_tools()
        messages = self._build_messages(task, context)
        actions_taken = []

        for _ in range(10):
            response: AIMessage = await llm_with_tools.ainvoke(messages)
            messages.append(response)
            if not response.tool_calls:
                break

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_fn = next((t for t in self.tools if t.name == tool_name), None)
                if tool_fn:
                    try:
                        result = await tool_fn.ainvoke(tool_args)
                        actions_taken.append({"action": tool_name, "args": tool_args})
                    except Exception as exc:
                        result = f"Error: {exc}"
                else:
                    result = f"Tool not found: {tool_name}"
                messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))

        final = messages[-1]
        output = final.content if isinstance(final, AIMessage) else str(final.content)
        return AgentResult(agent_name=self.name, success=True, output=output, actions_taken=actions_taken)
