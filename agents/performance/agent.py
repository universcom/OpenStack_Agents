"""
agents/performance/agent.py
────────────────────────────
Performance & Advisory Agent

Analyses historical metrics to produce actionable recommendations:
  - Over/under-provisioned instances
  - Cost optimisation opportunities
  - Bottleneck identification
  - Capacity planning
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import structlog
from langchain_core.messages import AIMessage, ToolMessage

from agents.base import AgentResult, BaseAgent
from tools.monitoring.prometheus import PROMETHEUS_TOOLS
from tools.openstack.nova import NOVA_TOOLS

logger = structlog.get_logger(__name__)

PERFORMANCE_SYSTEM_PROMPT = """You are an OpenStack performance engineer and cloud architect
specialising in capacity planning, cost optimisation, and performance tuning.

## Your analysis framework
1. **Utilisation audit**: Compare allocated vs actual resource usage (CPU, RAM, disk, network)
2. **Rightsizing**: Flag over/under-provisioned instances with specific resize recommendations
3. **Bottleneck detection**: Identify saturation points (CPU steal, memory pressure, I/O wait)
4. **Capacity forecasting**: Project when current capacity will be exhausted
5. **Cost efficiency**: Calculate waste and prioritise optimisation opportunities by ROI

## Report format
Always produce:
- **Executive summary** (3 bullet points max)
- **Findings table** with severity (🔴 Critical / 🟡 Warning / 🟢 Info)
- **Prioritised recommendations** with estimated impact
- **Quick wins** (changes that can be made today with low risk)

## Data sources
Use Prometheus to query 7-day and 30-day metric trends for accurate baselines.
Compare p50, p95, and p99 to understand true workload peaks vs averages.
"""


class PerformanceAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "PerformanceAgent"

    @property
    def system_prompt(self) -> str:
        return PERFORMANCE_SYSTEM_PROMPT

    @property
    def tools(self):
        return PROMETHEUS_TOOLS + NOVA_TOOLS

    async def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> AgentResult:
        self._log.info("performance_agent_run", task_preview=task[:80])
        llm_with_tools = self._bind_tools()
        messages = self._build_messages(task, context)
        actions_taken = []

        for _ in range(10):
            response: AIMessage = await llm_with_tools.ainvoke(messages)
            messages.append(response)
            if not response.tool_calls:
                break
            for tool_call in response.tool_calls:
                tool_fn = next((t for t in self.tools if t.name == tool_call["name"]), None)
                if tool_fn:
                    try:
                        result = await tool_fn.ainvoke(tool_call["args"])
                        actions_taken.append({"action": tool_call["name"], "args": tool_call["args"]})
                    except Exception as exc:
                        result = f"Error: {exc}"
                else:
                    result = f"Tool not found: {tool_call['name']}"
                messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))

        final = messages[-1]
        output = final.content if isinstance(final, AIMessage) else str(final.content)
        return AgentResult(agent_name=self.name, success=True, output=output, actions_taken=actions_taken)
