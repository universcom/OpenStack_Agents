"""
main.py
───────
Entry point for the OpenStack AI Agent system.

Modes:
  python main.py               → interactive CLI (default)
  python main.py --mode server → FastAPI server on configured port
  python main.py --mode demo   → run a demo conversation
"""
from __future__ import annotations

import asyncio
import sys
from typing import Optional

import structlog
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule

app = typer.Typer(add_completion=False)
console = Console()
logger = structlog.get_logger(__name__)


def _configure_logging(log_level: str = "INFO"):
    import logging
    import structlog

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
    )


# ── CLI mode ──────────────────────────────────────────────────────────────────

async def _run_cli(user_id: str, project_id: Optional[str]):
    from orchestrator.master import MasterOrchestrator

    orchestrator = MasterOrchestrator()
    session_id = None

    console.print(
        Panel.fit(
            "[bold cyan]OpenStack AI Agent[/bold cyan]\n"
            "[dim]Multi-agent system for OpenStack management[/dim]\n\n"
            "Type your request in natural language.\n"
            "Commands: [bold]exit[/bold] | [bold]clear[/bold] (reset session) | [bold]help[/bold]",
            border_style="cyan",
        )
    )
    console.print()

    while True:
        try:
            user_input = Prompt.ask("[bold green]You[/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            console.print("[dim]Goodbye.[/dim]")
            break

        if user_input.lower() == "clear":
            session_id = None
            console.print("[dim]Session cleared.[/dim]\n")
            continue

        if user_input.lower() == "help":
            console.print(
                Panel(
                    "**Examples:**\n"
                    "- Create a VM with 4 vCPUs and 8GB RAM\n"
                    "- List all my instances\n"
                    "- Why is my instance abc-123 not responding?\n"
                    "- What is the current CPU usage across the cluster?\n"
                    "- Give me performance recommendations for my project\n",
                    title="Help",
                    border_style="dim",
                )
            )
            continue

        with console.status("[dim]Thinking…[/dim]", spinner="dots"):
            result = await orchestrator.handle(
                message=user_input,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
            )

        session_id = result["session_id"]

        console.print()
        console.print(Rule("[dim]Agent[/dim]", style="dim"))
        console.print(Markdown(result["final_response"]))
        console.print()

        if result.get("pending_approvals"):
            console.print(
                "[yellow]⚠  One or more actions require your approval before they execute.[/yellow]"
            )

        if not result["success"]:
            console.print("[red]The agent encountered an error. See logs for details.[/red]")


# ── FastAPI server mode ───────────────────────────────────────────────────────

def _run_server(host: str, port: int):
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel as PydanticModel

    from orchestrator.master import MasterOrchestrator

    api = FastAPI(title="OpenStack AI Agent", version="0.1.0")
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _orchestrator = MasterOrchestrator()

    class ChatRequest(PydanticModel):
        message: str
        user_id: str = "anonymous"
        project_id: Optional[str] = None
        session_id: Optional[str] = None

    @api.post("/chat")
    async def chat(req: ChatRequest):
        result = await _orchestrator.handle(
            message=req.message,
            user_id=req.user_id,
            project_id=req.project_id,
            session_id=req.session_id,
        )
        return result

    @api.get("/health")
    async def health():
        return {"status": "ok"}

    console.print(f"[cyan]Starting API server on http://{host}:{port}[/cyan]")
    uvicorn.run(api, host=host, port=port)


# ── Demo mode ─────────────────────────────────────────────────────────────────

async def _run_demo():
    from orchestrator.master import MasterOrchestrator

    orchestrator = MasterOrchestrator()

    demo_messages = [
        ("alice", "proj-demo", "List all my running instances"),
        ("alice", "proj-demo", "Create a VM called web-server-01 with 2 vCPUs and 4GB RAM"),
        ("alice", "proj-demo", "What is the current CPU usage of the cluster?"),
        ("alice", "proj-demo", "Why is instance abc-123 in ERROR state?"),
        ("alice", "proj-demo", "Give me performance recommendations for my project"),
    ]

    console.print(Panel.fit("[bold]OpenStack AI Agent — Demo Mode[/bold]", border_style="cyan"))

    for user_id, project_id, message in demo_messages:
        console.print(f"\n[bold green]User:[/bold green] {message}")
        with console.status("[dim]Processing…[/dim]"):
            result = await orchestrator.handle(
                message=message, user_id=user_id, project_id=project_id
            )
        console.print(Rule("[dim]Agent response[/dim]", style="dim"))
        console.print(Markdown(result["final_response"]))


# ── CLI entry points ──────────────────────────────────────────────────────────

@app.command()
def main(
    mode: str = typer.Option("cli", "--mode", "-m", help="cli | server | demo"),
    user_id: str = typer.Option("engineer", "--user", "-u", help="User ID"),
    project_id: Optional[str] = typer.Option(None, "--project", "-p", help="OpenStack project ID"),
    log_level: str = typer.Option("WARNING", "--log-level", "-l", help="Logging level"),
):
    """OpenStack AI Agent — multi-agent infrastructure management."""
    _configure_logging(log_level)

    if mode == "cli":
        asyncio.run(_run_cli(user_id=user_id, project_id=project_id))
    elif mode == "server":
        from config.settings import get_settings
        settings = get_settings()
        _run_server(host=settings.api.host, port=settings.api.port)
    elif mode == "demo":
        asyncio.run(_run_demo())
    else:
        console.print(f"[red]Unknown mode: {mode}. Use cli | server | demo[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
