"""
tools/iac/ansible.py
────────────────────
LangChain tools for running Ansible playbooks.
ansible-playbook must be installed and on PATH.
"""
from __future__ import annotations
import asyncio, os
import structlog
from langchain_core.tools import tool
from config.settings import get_settings

logger = structlog.get_logger(__name__)

@tool("run_ansible_playbook")
async def run_ansible_playbook(playbook: str, inventory: str,
                                extra_vars: str = "", limit: str = "",
                                check_mode: bool = False) -> str:
    """
    Run an Ansible playbook. Set check_mode=True for a dry run (no changes applied).
    Args:
        playbook: Path to .yml playbook
        inventory: Path to inventory file or comma-separated hosts
        extra_vars: JSON string of extra variables
        limit: Restrict execution to specific hosts/groups
        check_mode: If True, simulate without making changes
    """
    settings = get_settings()
    use_check = settings.agent.dry_run or check_mode
    args = ["ansible-playbook", playbook, "-i", inventory]
    if use_check:
        args.append("--check")
    if extra_vars:
        args += ["--extra-vars", extra_vars]
    if limit:
        args += ["--limit", limit]
    try:
        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "ANSIBLE_NOCOLOR": "1"},
        )
        stdout, stderr = await proc.communicate()
        rc = proc.returncode
        label = "[CHECK MODE] " if use_check else ""
        if rc != 0:
            return f"{label}Playbook failed:\n{stderr.decode()[:2000]}"
        logger.info("ansible_playbook_ran", playbook=playbook)
        return f"{label}Playbook complete.\n{stdout.decode()[-1500:]}"
    except FileNotFoundError:
        return "ansible-playbook not found. Install Ansible and ensure it is on PATH."
    except Exception as exc:
        return f"Error running Ansible: {exc}"

ANSIBLE_TOOLS = [run_ansible_playbook]
