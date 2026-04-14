"""
orchestrator/master.py
──────────────────────
MasterOrchestrator: coordinates agent routing, session management, and response synthesis.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

import structlog

from agents.base import AgentResult
from agents.chatbot.agent import CustomerChatbotAgent
from agents.infra.agent import InfraManagementAgent
from agents.monitoring.agent import MonitoringAgent
from agents.performance.agent import PerformanceAgent
from agents.rca.agent import RCAAgent

logger = structlog.get_logger(__name__)


class MasterOrchestrator:
    """
    Master orchestrator that routes user requests to the appropriate agent(s).
    Manages session state, context, and response synthesis.
    """

    def __init__(self):
        """Initialize the master orchestrator with all available agents."""
        self.agents = {
            "chatbot": CustomerChatbotAgent(),
            "infra": InfraManagementAgent(),
            "monitoring": MonitoringAgent(),
            "performance": PerformanceAgent(),
            "rca": RCAAgent(),
        }
        self.sessions: Dict[str, Dict[str, Any]] = {}
        logger.info("MasterOrchestrator initialized", agents=list(self.agents.keys()))

    async def handle(
        self,
        message: str,
        user_id: str,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle a user request by routing to appropriate agent(s).

        Args:
            message: User's natural language request
            user_id: Identifier for the user
            project_id: OpenStack project ID (optional)
            session_id: Session ID for context continuity (optional)

        Returns:
            Dictionary with response, session info, and metadata
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = {
                "user_id": user_id,
                "project_id": project_id,
                "messages": [],
                "agent_results": [],
            }

        session = self.sessions.get(session_id, {})
        logger.info(
            "Processing request",
            session_id=session_id,
            user_id=user_id,
            project_id=project_id,
            message=message[:100],
        )

        try:
            # Route to appropriate agent(s) based on message content
            agent_name = self._route_message(message)
            agent = self.agents.get(agent_name, self.agents["chatbot"])

            # Prepare context for the agent
            context = {
                "user_id": user_id,
                "project_id": project_id,
                "session_id": session_id,
            }

            # Run the selected agent with correct interface
            agent_result = await agent.run(
                task=message,
                context=context,
                session_id=session_id,
            )

            # Store in session history
            session["messages"].append({"role": "user", "content": message})
            session["messages"].append({"role": "assistant", "content": agent_result.output})
            session["agent_results"].append(agent_result.to_dict())

            # Prepare response
            response = {
                "session_id": session_id,
                "final_response": agent_result.output,
                "success": agent_result.success,
                "agent": agent_result.agent_name,
                "pending_approvals": agent_result.requires_approval,
                "metadata": agent_result.metadata,
            }

            logger.info(
                "Request processed successfully",
                session_id=session_id,
                agent=agent_result.agent_name,
                success=agent_result.success,
            )

            return response

        except Exception as e:
            logger.error(
                "Error processing request",
                session_id=session_id,
                error=str(e),
                exc_info=True,
            )
            return {
                "session_id": session_id,
                "final_response": f"An error occurred: {str(e)}",
                "success": False,
                "agent": "error_handler",
                "pending_approvals": [],
                "metadata": {"error": str(e)},
            }

    def _route_message(self, message: str) -> str:
        """
        Route message to appropriate agent based on keywords and context.

        Args:
            message: User message to analyze

        Returns:
            Agent name to handle the request
        """
        message_lower = message.lower()

        # Route based on keywords
        if any(
            keyword in message_lower
            for keyword in [
                "create",
                "delete",
                "instance",
                "vm",
                "network",
                "storage",
                "volume",
            ]
        ):
            return "infra"
        elif any(
            keyword in message_lower
            for keyword in ["cpu", "memory", "disk", "performance", "recommend"]
        ):
            return "performance"
        elif any(
            keyword in message_lower
            for keyword in ["monitor", "alert", "metric", "prometheus", "status"]
        ):
            return "monitoring"
        elif any(
            keyword in message_lower
            for keyword in ["error", "issue", "why", "problem", "not working", "failing"]
        ):
            return "rca"
        else:
            return "chatbot"

    def clear_session(self, session_id: str) -> None:
        """Clear a session from memory."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info("Session cleared", session_id=session_id)
