"""
tools/openstack/cinder.py
─────────────────────────
LangChain tools for OpenStack Block Storage (Cinder).
Covers: volumes, snapshots, attachments.
"""
from __future__ import annotations
from typing import Optional
import openstack
import structlog
from langchain_core.tools import tool
from config.settings import get_settings

logger = structlog.get_logger(__name__)

def _get_conn():
    return openstack.connect(**get_settings().openstack.to_connection_params())


@tool("list_volumes")
async def list_volumes() -> str:
    """List all block storage volumes in the current project."""
    try:
        conn = _get_conn()
        volumes = list(conn.block_storage.volumes())
        if not volumes:
            return "No volumes found."
        lines = ["| Name | Size (GB) | Status | Attached to |"]
        lines.append("|------|-----------|--------|-------------|")
        for v in volumes:
            attachments = ", ".join(a.get("server_id", "")[:8] for a in v.attachments) or "—"
            lines.append(f"| {v.name or '—'} | {v.size} | {v.status} | {attachments} |")
        return f"Volumes ({len(volumes)}):\n\n" + "\n".join(lines)
    except Exception as exc:
        return f"Error listing volumes: {exc}"


@tool("create_volume")
async def create_volume(name: str, size_gb: int, volume_type: Optional[str] = None) -> str:
    """
    Create a new block storage volume.
    Args:
        name: Volume name
        size_gb: Size in gigabytes (1–10000)
        volume_type: Optional volume type (e.g. 'ssd', 'hdd')
    """
    settings = get_settings()
    if settings.agent.dry_run:
        return f"[DRY RUN] Would create {size_gb}GB volume '{name}'."
    try:
        conn = _get_conn()
        kwargs = {"name": name, "size": size_gb}
        if volume_type:
            kwargs["volume_type"] = volume_type
        vol = conn.block_storage.create_volume(**kwargs)
        logger.info("cinder_create_volume", name=name, size=size_gb, id=vol.id)
        return f"✅ Volume '{name}' ({size_gb}GB) created. ID: {vol.id} — Status: {vol.status}"
    except Exception as exc:
        return f"Error creating volume '{name}': {exc}"


@tool("delete_volume")
async def delete_volume(volume_id: str) -> str:
    """
    Delete a block storage volume by ID.
    DESTRUCTIVE — requires approval. Volume must be detached first.
    """
    settings = get_settings()
    if settings.agent.dry_run:
        return f"[DRY RUN] Would delete volume {volume_id}."
    try:
        conn = _get_conn()
        conn.block_storage.delete_volume(volume_id)
        logger.warning("cinder_delete_volume", volume_id=volume_id)
        return f"✅ Volume {volume_id} deletion initiated."
    except Exception as exc:
        return f"Error deleting volume {volume_id}: {exc}"


CINDER_TOOLS = [list_volumes, create_volume, delete_volume]
