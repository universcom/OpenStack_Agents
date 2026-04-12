"""
tools/iac/terraform.py
──────────────────────
LangChain tools wrapping Terraform CLI for IaC operations.
Terraform binary must be installed and on PATH.
"""
from __future__ import annotations
import asyncio, os
import structlog
from langchain_core.tools import tool
from config.settings import get_settings

logger = structlog.get_logger(__name__)

async def _run_terraform(args: list, cwd: str):
    proc = await asyncio.create_subprocess_exec(
        "terraform", *args, cwd=cwd,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        env={**os.environ, "TF_IN_AUTOMATION": "1"},
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode(), stderr.decode()

@tool("terraform_plan")
async def terraform_plan(working_dir: str, var_file: str = "") -> str:
    """Run 'terraform plan' in the specified directory (read-only preview). Always call before terraform_apply."""
    if get_settings().agent.dry_run:
        return f"[DRY RUN] Would run: terraform plan in {working_dir}"
    args = ["plan", "-no-color", "-input=false"]
    if var_file:
        args += ["-var-file", var_file]
    rc, stdout, stderr = await _run_terraform(args, working_dir)
    if rc != 0:
        return f"Terraform plan failed:\n{stderr[:2000]}"
    summary = next((l for l in stdout.splitlines() if "Plan:" in l or "No changes" in l), "")
    return f"Terraform plan succeeded.\n{summary}\n\n{stdout[-2000:]}"

@tool("terraform_apply")
async def terraform_apply(working_dir: str, var_file: str = "") -> str:
    """Run 'terraform apply'. DESTRUCTIVE — modifies real infrastructure. Requires prior approval."""
    if get_settings().agent.dry_run:
        return f"[DRY RUN] Would run: terraform apply in {working_dir}"
    args = ["apply", "-auto-approve", "-no-color", "-input=false"]
    if var_file:
        args += ["-var-file", var_file]
    rc, stdout, stderr = await _run_terraform(args, working_dir)
    logger.warning("terraform_apply_executed", working_dir=working_dir)
    if rc != 0:
        return f"Terraform apply failed:\n{stderr[:2000]}"
    summary = next((l for l in stdout.splitlines() if "Apply complete" in l), "")
    return f"Terraform apply complete.\n{summary}"

TERRAFORM_TOOLS = [terraform_plan, terraform_apply]
