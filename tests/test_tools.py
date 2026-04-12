"""
tests/test_tools.py
────────────────────
Unit tests for OpenStack and monitoring tools.
Uses mocks — no live API connections needed.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Nova tool tests ───────────────────────────────────────────────────────────

class TestNovaTools:

    @pytest.mark.asyncio
    @patch("tools.openstack.nova._get_conn")
    async def test_list_instances_empty(self, mock_conn):
        """list_instances returns a message when there are no VMs."""
        mock_conn.return_value.compute.servers.return_value = []
        from tools.openstack.nova import list_instances
        result = await list_instances.ainvoke({"limit": 10})
        assert "No instances found" in result

    @pytest.mark.asyncio
    @patch("tools.openstack.nova._get_conn")
    async def test_list_flavors(self, mock_conn):
        """list_flavors returns a formatted table."""
        flavor = MagicMock()
        flavor.name = "m1.small"
        flavor.vcpus = 1
        flavor.ram = 2048
        flavor.disk = 20
        mock_conn.return_value.compute.flavors.return_value = [flavor]

        from tools.openstack.nova import list_flavors
        result = await list_flavors.ainvoke({})
        assert "m1.small" in result
        assert "1" in result  # vcpus

    @pytest.mark.asyncio
    @patch("tools.openstack.nova.get_settings")
    @patch("tools.openstack.nova._get_conn")
    async def test_create_instance_dry_run(self, mock_conn, mock_settings):
        """create_instance returns DRY RUN message when dry_run=True."""
        mock_settings.return_value.agent.dry_run = True
        from tools.openstack.nova import create_instance
        result = await create_instance.ainvoke({
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04",
            "network": "internal",
        })
        assert "DRY RUN" in result
        assert "test-vm" in result
        mock_conn.assert_not_called()

    @pytest.mark.asyncio
    @patch("tools.openstack.nova.get_settings")
    async def test_delete_instance_dry_run(self, mock_settings):
        """delete_instance is blocked in dry run mode."""
        mock_settings.return_value.agent.dry_run = True
        from tools.openstack.nova import delete_instance
        result = await delete_instance.ainvoke({"instance_id": "abc-123"})
        assert "DRY RUN" in result


# ── Prometheus tool tests ─────────────────────────────────────────────────────

class TestPrometheusTools:

    @pytest.mark.asyncio
    @patch("tools.monitoring.prometheus.httpx.AsyncClient")
    async def test_get_firing_alerts_none(self, mock_client_cls):
        """Returns healthy message when no alerts firing."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"data": {"alerts": []}}

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        from tools.monitoring.prometheus import get_firing_alerts
        result = await get_firing_alerts.ainvoke({})
        assert "No alerts" in result or "Healthy" in result or "firing" in result.lower()

    @pytest.mark.asyncio
    @patch("tools.monitoring.prometheus.httpx.AsyncClient")
    async def test_get_firing_alerts_with_alerts(self, mock_client_cls):
        """Returns alert details when alerts are firing."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "alerts": [
                    {
                        "state": "firing",
                        "labels": {"alertname": "HighCPU", "severity": "critical"},
                        "annotations": {"summary": "CPU over 90%"},
                    }
                ]
            }
        }
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        from tools.monitoring.prometheus import get_firing_alerts
        result = await get_firing_alerts.ainvoke({})
        assert "HighCPU" in result
        assert "CRITICAL" in result


# ── Agent result tests ────────────────────────────────────────────────────────

class TestAgentResult:

    def test_to_dict_structure(self):
        from agents.base import AgentResult
        result = AgentResult(
            agent_name="TestAgent",
            success=True,
            output="All good.",
            actions_taken=[{"action": "list_instances", "args": {}}],
        )
        d = result.to_dict()
        assert d["agent"] == "TestAgent"
        assert d["success"] is True
        assert d["output"] == "All good."
        assert len(d["actions_taken"]) == 1
        assert "run_id" in d
        assert "timestamp" in d

    def test_requires_approval_list(self):
        from agents.base import AgentResult
        result = AgentResult(
            agent_name="RCAAgent",
            success=True,
            output="Found root cause.",
            requires_approval=[{"action": "reboot_instance", "resource": "vm-123"}],
        )
        assert len(result.requires_approval) == 1
        assert result.requires_approval[0]["action"] == "reboot_instance"
