"""
tools/openstack/nova.py
───────────────────────
LangChain tools wrapping the OpenStack Compute API (Nova).

Each tool is a @tool-decorated async function with a clear docstring
(used by the LLM to decide when to invoke it) and Pydantic input validation.
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
    """Return an authenticated OpenStack connection."""
    settings = get_settings()
    return openstack.connect(**settings.openstack.to_connection_params())


# ── Input schemas ────────────────────────────────────────────────────────────

class CreateInstanceInput(BaseModel):
    name: str = Field(..., description="Name for the new instance")
    flavor: str = Field(..., description="Flavor name or ID (e.g. 'm1.medium', 'c2.large')")
    image: str = Field(..., description="Image name or ID")
    network: str = Field(..., description="Network name or ID to attach the instance to")
    project_id: Optional[str] = Field(None, description="Target project ID (admin only)")
    keypair: Optional[str] = Field(None, description="SSH keypair name")
    security_groups: Optional[List[str]] = Field(None, description="Security group names")
    user_data: Optional[str] = Field(None, description="Cloud-init user-data script (base64)")
    availability_zone: Optional[str] = Field(None, description="Availability zone")
    count: int = Field(1, ge=1, le=20, description="Number of instances to create")


class DeleteInstanceInput(BaseModel):
    instance_id: str = Field(..., description="Instance UUID to delete")
    force: bool = Field(False, description="Force delete even if instance is in error state")


class ListInstancesInput(BaseModel):
    project_id: Optional[str] = Field(None, description="Filter by project ID")
    status: Optional[str] = Field(None, description="Filter by status (ACTIVE, SHUTOFF, ERROR, etc.)")
    limit: int = Field(50, ge=1, le=500, description="Maximum number of instances to return")


class RebootInstanceInput(BaseModel):
    instance_id: str = Field(..., description="Instance UUID to reboot")
    reboot_type: str = Field("SOFT", description="'SOFT' (graceful) or 'HARD' (force)")


class ResizeInstanceInput(BaseModel):
    instance_id: str = Field(..., description="Instance UUID to resize")
    new_flavor: str = Field(..., description="Target flavor name or ID")


# ── Tools ────────────────────────────────────────────────────────────────────

@tool("list_instances", args_schema=ListInstancesInput)
async def list_instances(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> str:
    """
    List OpenStack compute instances (VMs).
    Use this to find existing VMs, check their status, IPs, and flavors.
    """
    try:
        conn = _get_conn()
        filters = {"limit": limit}
        if project_id:
            filters["project_id"] = project_id
        if status:
            filters["status"] = status.upper()

        servers = list(conn.compute.servers(**filters))
        if not servers:
            return "No instances found matching the given filters."

        lines = ["| Name | ID | Status | Flavor | IP |"]
        lines.append("|------|----|----|--------|-----|")
        for s in servers:
            ip = next(
                (
                    addr["addr"]
                    for nets in s.addresses.values()
                    for addr in nets
                    if addr["version"] == 4
                ),
                "N/A",
            )
            lines.append(f"| {s.name} | {s.id[:8]}… | {s.status} | {s.flavor['original_name']} | {ip} |")

        return f"Found {len(servers)} instance(s):\n\n" + "\n".join(lines)

    except Exception as exc:
        logger.error("nova_list_instances_error", error=str(exc))
        return f"Error listing instances: {exc}"


@tool("get_instance", return_direct=False)
async def get_instance(instance_id: str) -> str:
    """
    Get detailed information about a specific OpenStack instance by its UUID.
    Returns status, flavor, image, IPs, metadata, and recent events.
    """
    try:
        conn = _get_conn()
        server = conn.compute.get_server(instance_id)
        if not server:
            return f"Instance {instance_id} not found."

        ips = {
            net: [a["addr"] for a in addrs]
            for net, addrs in server.addresses.items()
        }
        return (
            f"**Instance: {server.name}**\n"
            f"- ID: {server.id}\n"
            f"- Status: {server.status}\n"
            f"- Flavor: {server.flavor['original_name']}\n"
            f"- Image: {server.image.get('id', 'N/A')}\n"
            f"- Created: {server.created_at}\n"
            f"- IPs: {ips}\n"
            f"- Power state: {server.power_state}\n"
            f"- Availability zone: {server.availability_zone}\n"
        )
    except Exception as exc:
        logger.error("nova_get_instance_error", instance_id=instance_id, error=str(exc))
        return f"Error retrieving instance {instance_id}: {exc}"


@tool("create_instance", args_schema=CreateInstanceInput)
async def create_instance(
    name: str,
    flavor: str,
    image: str,
    network: str,
    project_id: Optional[str] = None,
    keypair: Optional[str] = None,
    security_groups: Optional[List[str]] = None,
    user_data: Optional[str] = None,
    availability_zone: Optional[str] = None,
    count: int = 1,
) -> str:
    """
    Create one or more OpenStack compute instances (VMs).
    Requires name, flavor, image, and network. Returns the new instance ID(s).
    """
    settings = get_settings()
    if settings.agent.dry_run:
        return (
            f"[DRY RUN] Would create {count} instance(s) named '{name}' "
            f"using flavor '{flavor}', image '{image}', network '{network}'."
        )

    try:
        conn = _get_conn()

        # Resolve names to IDs
        flavor_obj = conn.compute.find_flavor(flavor, ignore_missing=False)
        image_obj = conn.image.find_image(image, ignore_missing=False)
        network_obj = conn.network.find_network(network, ignore_missing=False)

        server_kwargs = {
            "name": name,
            "flavor_id": flavor_obj.id,
            "image_id": image_obj.id,
            "networks": [{"uuid": network_obj.id}],
        }
        if keypair:
            server_kwargs["key_name"] = keypair
        if security_groups:
            server_kwargs["security_groups"] = [{"name": sg} for sg in security_groups]
        if user_data:
            server_kwargs["user_data"] = user_data
        if availability_zone:
            server_kwargs["availability_zone"] = availability_zone
        if count > 1:
            server_kwargs["min_count"] = count
            server_kwargs["max_count"] = count

        server = conn.compute.create_server(**server_kwargs)
        logger.info("nova_create_instance", name=name, id=server.id)
        return (
            f"✅ Instance '{name}' created successfully.\n"
            f"- ID: {server.id}\n"
            f"- Status: {server.status}\n"
            f"It will be ACTIVE in 30–90 seconds."
        )
    except Exception as exc:
        logger.error("nova_create_instance_error", name=name, error=str(exc))
        return f"Error creating instance '{name}': {exc}"


@tool("delete_instance", args_schema=DeleteInstanceInput)
async def delete_instance(instance_id: str, force: bool = False) -> str:
    """
    Delete an OpenStack compute instance by UUID.
    DESTRUCTIVE — this action is irreversible. Guardrails require approval.
    """
    settings = get_settings()
    if settings.agent.dry_run:
        return f"[DRY RUN] Would delete instance {instance_id} (force={force})."

    try:
        conn = _get_conn()
        conn.compute.delete_server(instance_id, force=force)
        logger.warning("nova_delete_instance", instance_id=instance_id, force=force)
        return f"✅ Instance {instance_id} deletion initiated."
    except Exception as exc:
        logger.error("nova_delete_instance_error", instance_id=instance_id, error=str(exc))
        return f"Error deleting instance {instance_id}: {exc}"


@tool("reboot_instance", args_schema=RebootInstanceInput)
async def reboot_instance(instance_id: str, reboot_type: str = "SOFT") -> str:
    """
    Reboot an OpenStack compute instance.
    Use SOFT for graceful restart, HARD for force reboot (like pulling the power).
    """
    settings = get_settings()
    if settings.agent.dry_run:
        return f"[DRY RUN] Would {reboot_type} reboot instance {instance_id}."

    try:
        conn = _get_conn()
        conn.compute.reboot_server(instance_id, reboot_type=reboot_type)
        logger.info("nova_reboot_instance", instance_id=instance_id, type=reboot_type)
        return f"✅ {reboot_type} reboot initiated for instance {instance_id}."
    except Exception as exc:
        logger.error("nova_reboot_instance_error", instance_id=instance_id, error=str(exc))
        return f"Error rebooting instance {instance_id}: {exc}"


@tool("list_flavors")
async def list_flavors() -> str:
    """
    List all available compute flavors (VM sizes) with their vCPU, RAM, and disk specs.
    Use this before creating an instance to find an appropriate flavor.
    """
    try:
        conn = _get_conn()
        flavors = list(conn.compute.flavors())
        flavors.sort(key=lambda f: (f.vcpus, f.ram))

        lines = ["| Name | vCPUs | RAM (MB) | Disk (GB) |"]
        lines.append("|------|-------|----------|-----------|")
        for f in flavors:
            lines.append(f"| {f.name} | {f.vcpus} | {f.ram} | {f.disk} |")

        return f"Available flavors ({len(flavors)}):\n\n" + "\n".join(lines)
    except Exception as exc:
        logger.error("nova_list_flavors_error", error=str(exc))
        return f"Error listing flavors: {exc}"


# ── Tool registry ─────────────────────────────────────────────────────────────

NOVA_TOOLS = [
    list_instances,
    get_instance,
    create_instance,
    delete_instance,
    reboot_instance,
    list_flavors,
]
