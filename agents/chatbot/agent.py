"""
agents/chatbot/agent.py
────────────────────────
Customer Chatbot Agent

Handles natural-language requests from non-technical end-users:
  - Create / list / delete VMs
  - Manage networks, volumes, keypairs
  - Check status of their resources
  - Guided provisioning with clarifying questions

Uses ReAct-style tool calling: think → act → observe → respond.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agents.base import AgentResult, BaseAgent
from tools.openstack.nova import NOVA_TOOLS

logger = structlog.get_logger(__name__)

CHATBOT_SYSTEM_PROMPT = """You are **Nova**, a friendly and knowledgeable OpenStack assistant.
You help customers create, manage, and monitor their cloud resources through natural conversation.

## Your capabilities
- Create virtual machines (instances), networks, subnets, volumes, and security groups
- List and describe existing resources
- Check the status and health of instances
- Help customers choose the right VM size (flavor) for their workload
- Explain OpenStack concepts in simple terms

## Communication style
- Be warm, clear, and concise — customers may not be technical experts
- When you need more information (e.g. which network, which keypair), ask one clarifying question at a time
- Always confirm what you are about to do before executing any changes
- Present results in easy-to-read tables or bullet lists
- If an action requires approval (deletion, etc.), explain why and what will happen

## Constraints
- You can ONLY act on resources within the customer's own project
- You CANNOT perform bulk operations affecting more than 10 resources at once
- Always run in the customer's project context — never ask for or use other project credentials
- If a request is outside your scope (e.g. infrastructure-level changes), explain that and offer to escalate

## Safety
- Before any CREATE or DELETE action, summarise what you are about to do and ask for confirmation
- If you are unsure about an action, say so and offer alternatives
"""


class CustomerChatbotAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "CustomerChatbotAgent"

    @property
    def system_prompt(self) -> str:
        return CHATBOT_SYSTEM_PROMPT

    @property
    def tools(self):
        return NOVA_TOOLS

    async def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> AgentResult:
        self._log.info("chatbot_agent_run", task_preview=task[:80])

        llm_with_tools = self._bind_tools()
        messages = self._build_messages(task, context)
        actions_taken = []

        # ReAct loop: max 8 iterations to prevent runaway loops
        for iteration in range(8):
            response: AIMessage = await llm_with_tools.ainvoke(messages)
            messages.append(response)

            # No tool calls → final answer
            if not response.tool_calls:
                break

            # Execute each tool call
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                self._log_action(tool_name, tool_args)

                # Find and execute the tool
                tool_fn = next(
                    (t for t in self.tools if t.name == tool_name), None
                )
                if tool_fn is None:
                    tool_output = f"Tool '{tool_name}' not found."
                else:
                    try:
                        tool_output = await tool_fn.ainvoke(tool_args)
                        actions_taken.append(
                            {"action": tool_name, "args": tool_args, "result": str(tool_output)[:300]}
                        )
                    except Exception as exc:
                        tool_output = f"Tool error: {exc}"
                        self._log.error("chatbot_tool_error", tool=tool_name, error=str(exc))

                messages.append(
                    ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])
                )

        final_message = messages[-1]
        output = (
            final_message.content
            if isinstance(final_message, AIMessage)
            else str(final_message.content)
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            output=output,
            actions_taken=actions_taken,
        )
