"""
tools/openstack/neutron.py
──────────────────────────
LangChain tools for OpenStack Networking (Neutron).
Covers: networks, subnets, routers, floating IPs, security groups.
"""
from __future__ import annotations
from typing import List, Optional
import openstack
import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from config.settings import get_settings

logger = structlog.get_logger(__name__)

def _get_conn():
    return openstack.connect(**get_settings().openstack.to_connection_params())


@tool("list_networks")
async def list_networks() -> str:
    """List all OpenStack networks available to the current project."""
    try:
        conn = _get_conn()
        networks = list(conn.network.networks())
        if not networks:
            return "No networks found."
        lines = ["| Name | ID | Status | Shared |"]
        lines.append("|------|----|----|--------|")
        for n in networks:
            lines.append(f"| {n.name} | {n.id[:8]}… | {n.status} | {n.is_shared} |")
        return f"Networks ({len(networks)}):\n\n" + "\n".join(lines)
    except Exception as exc:
        return f"Error listing networks: {exc}"


@tool("create_network")
async def create_network(name: str, shared: bool = False) -> str:
    """
    Create a new OpenStack network.
    Args:
        name: Network name
        shared: Whether the network is shared across projects
    """
    settings = get_settings()
    if settings.agent.dry_run:
        return f"[DRY RUN] Would create network '{name}' (shared={shared})."
    try:
        conn = _get_conn()
        network = conn.network.create_network(name=name, is_shared=shared)
        logger.info("neutron_create_network", name=name, id=network.id)
        return f"✅ Network '{name}' created. ID: {network.id}"
    except Exception as exc:
        return f"Error creating network '{name}': {exc}"


@tool("list_security_groups")
async def list_security_groups() -> str:
    """List all security groups in the current project."""
    try:
        conn = _get_conn()
        sgs = list(conn.network.security_groups())
        if not sgs:
            return "No security groups found."
        lines = [f"- **{sg.name}** ({sg.id[:8]}…): {sg.description}" for sg in sgs]
        return "Security groups:\n\n" + "\n".join(lines)
    except Exception as exc:
        return f"Error listing security groups: {exc}"


NEUTRON_TOOLS = [list_networks, create_network, list_security_groups]
