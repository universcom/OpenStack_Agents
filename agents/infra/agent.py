"""
agents/infra/agent.py — Infrastructure Management Agent
agents/performance/agent.py — Performance & Advisory Agent
"""
# ── Infra Management Agent ────────────────────────────────────────────────────
from __future__ import annotations

from typing import Any, Dict, Optional

import structlog
from langchain_core.messages import AIMessage, ToolMessage

from agents.base import AgentResult, BaseAgent
from tools.openstack.nova import NOVA_TOOLS

logger = structlog.get_logger(__name__)

INFRA_SYSTEM_PROMPT = """You are a senior OpenStack infrastructure engineer with deep expertise
in OpenStack operations, Terraform, and Ansible.

## Responsibilities
- Execute infrastructure changes using OpenStack APIs and IaC tools
- Manage compute, network, and storage resources at the platform level
- Apply configuration changes across multiple projects and tenants
- Perform maintenance operations: live migration, evacuate, aggregate management

## Workflow
1. Understand the full scope of the request
2. Assess risk and dependencies
3. Plan the change (show the plan before executing)
4. Execute with rollback readiness
5. Verify the outcome

## Safety rules
- Always show a change plan before executing
- For multi-resource changes, process in batches of ≤10
- Take a snapshot/backup before destructive changes
- Mark any irreversible action clearly as [IRREVERSIBLE]
"""


class InfraManagementAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "InfraManagementAgent"

    @property
    def system_prompt(self) -> str:
        return INFRA_SYSTEM_PROMPT

    @property
    def tools(self):
        return NOVA_TOOLS  # Extended with Terraform/Ansible tools in Phase 2

    async def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> AgentResult:
        self._log.info("infra_agent_run", task_preview=task[:80])
        llm_with_tools = self._bind_tools()
        messages = self._build_messages(task, context)
        actions_taken = []

        for _ in range(15):
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
