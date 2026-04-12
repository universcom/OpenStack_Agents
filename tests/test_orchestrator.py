"""
tests/test_orchestrator.py
──────────────────────────
Unit tests for the orchestrator router and guardrails.
These tests run without an OpenStack connection or Anthropic API key.
"""
from __future__ import annotations

import pytest

from orchestrator.guardrails import GuardrailCheck, _DESTRUCTIVE_RE, _mentions_other_project
from orchestrator.router import IntentRouter, RoutingDecision, KEYWORD_SHORTCUTS


# ── Router tests ──────────────────────────────────────────────────────────────

class TestKeywordShortcut:

    def setup_method(self):
        self.router = IntentRouter.__new__(IntentRouter)

    def test_monitoring_keyword(self):
        result = self.router._keyword_shortcut("What is the CPU usage right now?")
        assert result == "monitoring"

    def test_rca_keyword(self):
        result = self.router._keyword_shortcut("Why is my instance failing?")
        assert result == "rca"

    def test_performance_keyword(self):
        result = self.router._keyword_shortcut("Can you recommend optimizations for my infra?")
        assert result == "performance"

    def test_infra_keyword(self):
        result = self.router._keyword_shortcut("Run the Terraform plan for this change")
        assert result == "infra"

    def test_no_shortcut(self):
        result = self.router._keyword_shortcut("Create a VM for me please")
        assert result is None  # Falls through to LLM classification


class TestRoutingDecision:

    def test_from_dict_valid(self):
        data = {
            "primary_agent": "chatbot",
            "secondary_agents": ["monitoring"],
            "confidence": 0.92,
            "intent_summary": "User wants to create a VM",
            "is_destructive": False,
        }
        decision = RoutingDecision.from_dict(data)
        assert decision.primary_agent == "chatbot"
        assert decision.confidence == 0.92
        assert "monitoring" in decision.secondary_agents

    def test_fallback(self):
        decision = RoutingDecision.fallback()
        assert decision.primary_agent == "chatbot"
        assert decision.confidence == 0.5


# ── Guardrail tests ───────────────────────────────────────────────────────────

class TestDestructivePattern:

    def test_delete_detected(self):
        assert _DESTRUCTIVE_RE.search("please delete the instance abc-123")

    def test_destroy_detected(self):
        assert _DESTRUCTIVE_RE.search("destroy all volumes in the project")

    def test_reboot_detected(self):
        assert _DESTRUCTIVE_RE.search("reboot the server immediately")

    def test_list_not_destructive(self):
        assert not _DESTRUCTIVE_RE.search("list all my running instances")

    def test_create_not_destructive(self):
        assert not _DESTRUCTIVE_RE.search("create a new VM with 4 vCPUs")


class TestCrossProjectScope:

    def test_same_project_ok(self):
        result = _mentions_other_project(
            "create a VM in project_id=abc123", "abc123"
        )
        assert not result

    def test_different_project_flagged(self):
        result = _mentions_other_project(
            "please access project_id=999-different-project", "abc123"
        )
        assert result

    def test_no_project_in_message(self):
        result = _mentions_other_project("just create me a VM", "abc123")
        assert not result
