"""
agents/rca/agent.py
────────────────────
Root Cause Analysis (RCA) & Remediation Agent

Investigates OpenStack errors and incidents by:
  1. Querying recent logs from OpenSearch
  2. Correlating with Prometheus metrics
  3. Checking instance/service status
  4. Generating a structured RCA report
  5. Proposing (and optionally executing) remediation steps

Output is a structured RCA report with:
  - Likely root cause (confidence-rated)
  - Timeline of events
  - Affected resources
  - Recommended fixes
  - Preventative measures
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog
from langchain_core.messages import AIMessage, ToolMessage

from agents.base import AgentResult, BaseAgent
from tools.monitoring.prometheus import PROMETHEUS_TOOLS
from tools.openstack.nova import NOVA_TOOLS

logger = structlog.get_logger(__name__)

RCA_SYSTEM_PROMPT = """You are an expert OpenStack Site Reliability Engineer specialising in
root cause analysis (RCA) and incident remediation.

## Your mission
When given an error, alert, or incident description:
1. **Investigate**: Query logs, metrics, and resource status systematically
2. **Correlate**: Find patterns across multiple data sources
3. **Diagnose**: Identify the root cause with a confidence level
4. **Report**: Produce a clear, structured RCA report
5. **Remediate**: Propose specific remediation steps (and execute approved ones)

## Investigation methodology
- Start broad (check all firing alerts, recent errors in logs)
- Narrow down by time window and affected resource
- Correlate metric spikes with log events
- Check dependencies (network → compute → storage)
- Look for cascading failures

## RCA report format
Always structure your final response as:

### Root Cause Analysis Report

**Incident**: <one-line summary>
**Severity**: Critical / High / Medium / Low
**Confidence**: High / Medium / Low

#### Root Cause
<specific technical explanation of what went wrong and why>

#### Timeline
- HH:MM — event
- HH:MM — event

#### Affected Resources
- <resource type>: <name/ID>

#### Evidence
<key log lines, metric values, or observations that support your diagnosis>

#### Recommended Actions
1. **Immediate**: <fix now>
2. **Short-term**: <fix within 24h>
3. **Long-term**: <prevent recurrence>

## Constraints
- Be precise: cite specific log lines, metric values, timestamps
- Rate your confidence honestly (don't speculate without evidence)
- Flag when you need more data rather than guessing
- Mark any remediation action as [REQUIRES APPROVAL] if it is destructive
"""


class RCAAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "RCAAgent"

    @property
    def system_prompt(self) -> str:
        return RCA_SYSTEM_PROMPT

    @property
    def tools(self):
        # RCA needs both monitoring tools and compute tools
        return PROMETHEUS_TOOLS + NOVA_TOOLS

    async def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> AgentResult:
        self._log.info("rca_agent_run", task_preview=task[:80])

        llm_with_tools = self._bind_tools()
        messages = self._build_messages(task, context)
        actions_taken = []
        requires_approval = []

        for iteration in range(12):  # RCA may need more investigation steps
            response: AIMessage = await llm_with_tools.ainvoke(messages)
            messages.append(response)

            if not response.tool_calls:
                break

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Check if this tool action requires approval
                if self._requires_approval(tool_name):
                    requires_approval.append(
                        {"action": tool_name, "args": tool_args, "resource": tool_args.get("instance_id", "unknown")}
                    )
                    tool_output = f"[PENDING APPROVAL] Action '{tool_name}' requires human approval before execution."
                else:
                    tool_fn = next((t for t in self.tools if t.name == tool_name), None)
                    if tool_fn:
                        try:
                            tool_output = await tool_fn.ainvoke(tool_args)
                            actions_taken.append({"action": tool_name, "args": tool_args})
                        except Exception as exc:
                            tool_output = f"Tool error ({tool_name}): {exc}"
                    else:
                        tool_output = f"Tool '{tool_name}' not available."

                messages.append(
                    ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])
                )

        final = messages[-1]
        output = final.content if isinstance(final, AIMessage) else str(final.content)

        return AgentResult(
            agent_name=self.name,
            success=True,
            output=output,
            actions_taken=actions_taken,
            requires_approval=requires_approval,
        )
