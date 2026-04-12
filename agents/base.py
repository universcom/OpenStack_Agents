"""
agents/base.py
─────────────
BaseAgent: the common contract all specialized agents inherit.
Provides tool registration, LLM binding, structured logging, and
a standard async `run()` interface.
"""
from __future__ import annotations

import abc
import time
import uuid
from typing import Any, Dict, List, Optional, Sequence

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from config.settings import get_settings

logger = structlog.get_logger(__name__)


class AgentResult:
    """Structured return value from every agent run."""

    def __init__(
        self,
        agent_name: str,
        success: bool,
        output: str,
        actions_taken: Optional[List[Dict]] = None,
        requires_approval: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None,
    ):
        self.agent_name = agent_name
        self.success = success
        self.output = output
        self.actions_taken = actions_taken or []
        self.requires_approval = requires_approval or []
        self.metadata = metadata or {}
        self.run_id = str(uuid.uuid4())
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "agent": self.agent_name,
            "success": self.success,
            "output": self.output,
            "actions_taken": self.actions_taken,
            "requires_approval": self.requires_approval,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class BaseAgent(abc.ABC):
    """
    Abstract base for all OpenStack AI agents.

    Subclasses must implement:
    - `name` (property)
    - `system_prompt` (property)
    - `tools` (property) — list of LangChain tools
    - `run(task, context)` (method)
    """

    def __init__(self):
        self._settings = get_settings()
        self._log = structlog.get_logger(self.__class__.__name__)

        self._llm = ChatAnthropic(
            model=self._settings.agent.claude_model,
            api_key=self._settings.agent.anthropic_api_key,
            max_tokens=4096,
            temperature=0,  # deterministic for infra tasks
        )

    # ── Abstract interface ──────────────────────────────────────────────────

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable agent name, e.g. 'InfraManagementAgent'."""

    @property
    @abc.abstractmethod
    def system_prompt(self) -> str:
        """System prompt that defines this agent's role and constraints."""

    @property
    @abc.abstractmethod
    def tools(self) -> List[BaseTool]:
        """LangChain tools available to this agent."""

    @abc.abstractmethod
    async def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> AgentResult:
        """
        Execute the agent on a given task.

        Args:
            task:       Natural-language task description.
            context:    Optional structured context (user info, project, etc.)
            session_id: Optional session ID for memory continuity.

        Returns:
            AgentResult with output, actions taken, and any pending approvals.
        """

    # ── Shared helpers ──────────────────────────────────────────────────────

    def _build_messages(
        self,
        task: str,
        context: Optional[Dict] = None,
        history: Optional[List[BaseMessage]] = None,
    ) -> List[BaseMessage]:
        """Assemble a message list for the LLM call."""
        messages: List[BaseMessage] = [SystemMessage(content=self.system_prompt)]

        if history:
            messages.extend(history)

        user_content = task
        if context:
            import json
            ctx_str = json.dumps(context, indent=2, default=str)
            user_content = f"<context>\n{ctx_str}\n</context>\n\n{task}"

        messages.append(HumanMessage(content=user_content))
        return messages

    def _bind_tools(self) -> ChatAnthropic:
        """Return LLM with tools bound (for tool-calling loop)."""
        if self.tools:
            return self._llm.bind_tools(self.tools)
        return self._llm

    def _log_action(self, action: str, params: Dict, result: Any = None, error: str = None):
        """Emit a structured log entry for every action attempted."""
        self._log.info(
            "agent_action",
            agent=self.name,
            action=action,
            params=params,
            result=str(result)[:500] if result else None,
            error=error,
            dry_run=self._settings.agent.dry_run,
        )

    def _is_dry_run(self) -> bool:
        return self._settings.agent.dry_run

    def _requires_approval(self, action_name: str) -> bool:
        return action_name in self._settings.agent.approval_required

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} tools={len(self.tools)}>"
