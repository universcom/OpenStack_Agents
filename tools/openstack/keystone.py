"""
tools/openstack/keystone.py
───────────────────────────
LangChain tools for OpenStack Identity (Keystone).
Covers: projects, users, roles.
"""
from __future__ import annotations
import openstack
from langchain_core.tools import tool
from config.settings import get_settings

def _get_conn():
    return openstack.connect(**get_settings().openstack.to_connection_params())


@tool("list_projects")
async def list_projects() -> str:
    """List all OpenStack projects (tenants) visible to the current user."""
    try:
        conn = _get_conn()
        projects = list(conn.identity.projects())
        lines = [f"- **{p.name}** ({p.id[:8]}…) — {'enabled' if p.is_enabled else 'disabled'}" for p in projects]
        return f"Projects ({len(projects)}):\n\n" + "\n".join(lines)
    except Exception as exc:
        return f"Error listing projects: {exc}"


@tool("get_project_quota")
async def get_project_quota(project_id: str) -> str:
    """
    Get compute and storage quota usage for a specific project.
    Args:
        project_id: The OpenStack project UUID
    """
    try:
        conn = _get_conn()
        quota = conn.compute.get_quota_set(project_id)
        used = conn.compute.get_quota_set(project_id, usage=True)
        return (
            f"**Quota for project {project_id[:8]}…**\n\n"
            f"| Resource | Used | Limit |\n"
            f"|----------|------|-------|\n"
            f"| Instances | {used.instances.in_use} | {quota.instances} |\n"
            f"| vCPUs | {used.cores.in_use} | {quota.cores} |\n"
            f"| RAM (MB) | {used.ram.in_use} | {quota.ram} |\n"
            f"| Floating IPs | {used.floating_ips.in_use} | {quota.floating_ips} |\n"
        )
    except Exception as exc:
        return f"Error getting quota for project {project_id}: {exc}"


KEYSTONE_TOOLS = [list_projects, get_project_quota]
