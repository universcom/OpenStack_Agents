"""
tools/openstack/glance.py
─────────────────────────
LangChain tools for OpenStack Image Service (Glance).
"""
from __future__ import annotations
import openstack
from langchain_core.tools import tool
from config.settings import get_settings

def _get_conn():
    return openstack.connect(**get_settings().openstack.to_connection_params())


@tool("list_images")
async def list_images() -> str:
    """List all available OS images that can be used to create instances."""
    try:
        conn = _get_conn()
        images = list(conn.image.images())
        if not images:
            return "No images found."
        lines = ["| Name | ID | Status | Size |"]
        lines.append("|------|----|----|------|")
        for img in images[:30]:
            size_mb = f"{img.size // 1024 // 1024}MB" if img.size else "N/A"
            lines.append(f"| {img.name} | {img.id[:8]}… | {img.status} | {size_mb} |")
        return "Available images:\n\n" + "\n".join(lines)
    except Exception as exc:
        return f"Error listing images: {exc}"


GLANCE_TOOLS = [list_images]
