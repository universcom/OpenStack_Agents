"""
main.py
───────
Entry point for the OpenStack AI Agent system.

This file wires together three runtime modes and delegates all heavy lifting
to orchestrator.master.MasterOrchestrator.  Nothing OpenStack-specific lives
here — keep it thin.

Modes:
  python main.py               → interactive CLI (default)
  python main.py --mode server → FastAPI server on configured port
  python main.py --mode demo   → run a scripted demo conversation
"""
# Enables PEP 563 postponed evaluation of annotations — allows using class names
# as type hints before they are defined (e.g. referencing a class inside itself).
# Required for forward references and cleaner type hint syntax across Python 3.7+.
from __future__ import annotations

# asyncio is Python's built-in library for writing concurrent code using async/await.
# Used here to run the async CLI and demo functions from the synchronous main() entry point.
import asyncio

# sys provides access to interpreter internals — used here to direct log output to stdout.
import sys

# Optional[X] is shorthand for "either X or None" — used for parameters that may be omitted,
# such as project_id and session_id which default to None when not provided by the user.
from typing import Optional

# structlog gives structured, context-aware logging on top of stdlib logging.
import structlog
# typer builds the CLI from typed function signatures — no argparse boilerplate.
import typer

# Rich is a third-party library that adds colour, formatting, and layout to terminal output.
# It replaces plain print() calls with styled text, tables, progress bars, panels, and more,
# making the CLI visually clear without any manual ANSI escape codes.
from rich.console import Console   # main output renderer; handles colour, width, and stderr/stdout routing
from rich.markdown import Markdown  # renders Markdown text (headings, code blocks, lists) in the terminal
from rich.panel import Panel        # draws a bordered box around content — used for banners and help text
from rich.prompt import Prompt      # interactive input line with styled label (e.g. "You ▶")
from rich.rule import Rule          # prints a horizontal divider line, optionally with a centred label

# Typer app; shell completion disabled because the agent is interactive, not scripted.
app = typer.Typer(add_completion=False)

# Single shared Console so all output goes through the same Rich renderer.
console = Console()

# Module-level logger; each log record automatically carries the module name.
logger = structlog.get_logger(__name__)


# ── Logging setup ─────────────────────────────────────────────────────────────
#
# Configures the application's two-layer logging stack: stdlib logging as the
# transport backend and structlog as the enrichment/formatting frontend.
# Every log record produced anywhere in the codebase — including third-party
# libraries — is captured, timestamped, and printed to stdout in a coloured,
# human-readable format.  Must be called once at startup before any imports
# that might emit log records.
def _configure_logging(log_level: str = "INFO"):
    """
    Set up stdlib logging and structlog to write human-readable output to stdout.

    Two-layer setup:
      1. stdlib logging  — acts as the backend transport (writes bytes to stdout).
      2. structlog       — acts as the frontend pipeline (enriches and formats records
                           before handing them off to the stdlib backend).

    Called once at startup before any other code runs so that every log record
    emitted later (including from imported modules) is captured consistently.

    Args:
        log_level: Minimum severity to emit. Accepts any stdlib level name
                   ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
                   Defaults to "INFO"; the CLI exposes this via --log-level.
    """
    # Imported locally so that modules which import main.py at the top level
    # do not trigger logging configuration as a side effect.
    import logging
    import structlog

    # ── stdlib logging setup ─────────────────────────────────────────────────
    # Route all stdlib log records to stdout in plain-text format.
    # format="%(message)s" strips the default "INFO:root:…" prefix because
    # structlog's ConsoleRenderer already formats the full line.
    # getattr(..., logging.INFO) is a safe fallback if an unknown level name
    # is passed — avoids crashing on a typo like "VERBOS".
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    # ── structlog pipeline setup ─────────────────────────────────────────────
    # structlog processes each log call through a list of "processors" in order.
    # Each processor receives the event dict, may modify it, and passes it on.
    # The last processor must return a string (or bytes) for the logger factory.
    structlog.configure(
        processors=[
            # Step 1 — Pull any context variables bound via structlog.contextvars
            # (e.g. request_id, user_id set at the start of a request) into the
            # event dict so they appear on every record within that async context.
            structlog.contextvars.merge_contextvars,

            # Step 2 — Add the "level" key ("info", "warning", …) to the dict
            # so the renderer can display and colour it.
            structlog.processors.add_log_level,

            # Step 3 — Stamp each record with the current UTC time in ISO-8601
            # format (e.g. "2024-06-01T12:00:00.123456Z") for easy log parsing.
            structlog.processors.TimeStamper(fmt="iso"),

            # Step 4 — Convert the enriched dict into a coloured, human-readable
            # string and write it to the configured output stream.
            structlog.dev.ConsoleRenderer(),
        ],

        # make_filtering_bound_logger compiles a logger class at import time that
        # short-circuits calls below the threshold before they enter the processor
        # pipeline — cheaper than letting stdlib filter them after formatting.
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),

        # PrintLoggerFactory creates simple loggers that write directly to stdout,
        # consistent with the basicConfig stream above.
        logger_factory=structlog.PrintLoggerFactory(),
    )


# ── CLI mode ──────────────────────────────────────────────────────────────────
#
# Starts an interactive Read-Eval-Print Loop (REPL) in the terminal.
# The user types natural-language requests; each one is forwarded to
# MasterOrchestrator and the response is printed as formatted Markdown.
# Built-in commands (exit, clear, help) are resolved locally without touching
# the orchestrator.  A shared session_id keeps all turns in one conversation
# so the agent retains memory across messages.
async def _run_cli(user_id: str, project_id: Optional[str]):
    """
    Run the agent as an interactive terminal chat session.

    Keeps a single MasterOrchestrator alive for the entire session so that
    internal state (loaded tools, cached clients, etc.) is reused across turns.

    Args:
        user_id:    Identifies the operator for audit logging and per-user quotas.
        project_id: Scopes all OpenStack API calls to a specific tenant project.
                    If None, the orchestrator uses its configured default project.
    """
    # Deferred import: only CLI mode needs the orchestrator at startup.
    # Server and demo modes import it independently in their own functions.
    from orchestrator.master import MasterOrchestrator

    # Create one orchestrator for the whole session.
    # This is intentional — the orchestrator caches OpenStack clients, loaded
    # agent tools, and conversation state internally.  Re-creating it on every
    # turn would be slow and would lose in-memory context.
    orchestrator = MasterOrchestrator()

    # session_id ties multiple turns into a single conversation thread.
    # It starts as None so the orchestrator creates a new session on the first
    # call, then we store and forward the returned id on every subsequent turn.
    session_id = None

    # Print the welcome banner once at startup so the user knows the agent is
    # ready.  Panel.fit auto-sizes the box to the content width.
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

    # ── REPL loop ────────────────────────────────────────────────────────────
    # This loop runs forever until the user types "exit" or closes stdin.
    # Each iteration is one conversation turn: read → process → display.
    while True:

        # Read one line of input from the user.
        # Prompt.ask blocks until the user presses Enter.
        try:
            user_input = Prompt.ask("[bold green]You[/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            # EOFError  — stdin was a pipe or file and has been fully consumed
            #             (e.g. `echo "list VMs" | python main.py`).
            # KeyboardInterrupt — user pressed Ctrl-C in the terminal.
            # Both cases mean "stop the loop cleanly" without a traceback.
            console.print("\n[dim]Goodbye.[/dim]")
            break

        # Silently skip empty input — pressing Enter with no text should not
        # send a blank message to the orchestrator or waste an API call.
        if not user_input:
            continue

        # ── built-in CLI commands ─────────────────────────────────────────────
        # These are handled here (in the UI layer) and never reach the orchestrator.

        # "exit" / "quit" / "q" — terminate the session gracefully.
        if user_input.lower() in ("exit", "quit", "q"):
            console.print("[dim]Goodbye.[/dim]")
            break

        # "clear" — reset the conversation so the next message starts fresh.
        # Setting session_id to None causes the orchestrator to open a new session
        # on the very next call, discarding the previous conversation history.
        if user_input.lower() == "clear":
            session_id = None
            console.print("[dim]Session cleared.[/dim]\n")
            continue

        # "help" — print example prompts without contacting the orchestrator.
        # The examples cover the main agent capabilities so new users know what
        # kinds of requests are supported.
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

        # ── send message to the orchestrator ─────────────────────────────────
        # Everything that reaches this point is a real natural-language request.

        # Show an animated spinner while waiting for the orchestrator to respond.
        # This can take several seconds when multiple sub-agents are involved
        # (e.g. a monitoring agent + a VM agent called in parallel).
        with console.status("[dim]Thinking…[/dim]", spinner="dots"):
            result = await orchestrator.handle(
                message=user_input,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,   # None on first turn → creates new session
            )

        # Store the session_id returned by the orchestrator so the next turn
        # continues in the same conversation thread (same memory, same context).
        session_id = result["session_id"]

        # ── display the response ──────────────────────────────────────────────

        # Print a horizontal rule to visually separate the agent's reply from
        # the user's input, then render the response as Markdown so that
        # headings, bullet lists, and code blocks display correctly.
        console.print()
        console.print(Rule("[dim]Agent[/dim]", style="dim"))
        console.print(Markdown(result["final_response"]))
        console.print()

        # If the orchestrator has queued one or more actions that require the
        # user's explicit approval before executing (e.g. deleting a volume,
        # rebooting an instance), surface a warning so the user knows to look
        # for an approval prompt in the next turn.
        if result.get("pending_approvals"):
            console.print(
                "[yellow]⚠  One or more actions require your approval before they execute.[/yellow]"
            )

        # Surface agent-level errors without crashing the loop.
        # The user can rephrase their request or ask what went wrong.
        # Detailed stack traces are written to the log stream, not the console.
        if not result["success"]:
            console.print("[red]The agent encountered an error. See logs for details.[/red]")


# ── FastAPI server mode ───────────────────────────────────────────────────────
#
# Launches a FastAPI HTTP server that exposes the agent as a REST API.
# Two endpoints are registered: POST /chat accepts a message and returns the
# agent's structured response; GET /health is a liveness probe for load
# balancers.  A single MasterOrchestrator instance is shared across all
# requests to avoid re-initialisation overhead.  All heavy framework imports
# (FastAPI, uvicorn, pydantic) are deferred inside this function so other
# modes pay no startup cost for them.
def _run_server(host: str, port: int):
    """
    Expose the agent over HTTP so external clients (UIs, scripts, other services)
    can call it without running the CLI.

    All heavy imports are local so that `python main.py --mode cli` doesn't pay
    the FastAPI/uvicorn import cost.

    Args:
        host: Network interface to bind to. "0.0.0.0" listens on all interfaces;
              use "127.0.0.1" to restrict to localhost only.
        port: TCP port number the server listens on (default 8080).
    """
    # All framework imports are deferred inside this function.
    # If the user runs in cli or demo mode, none of these heavy packages
    # (FastAPI, uvicorn, pydantic) are imported, keeping startup time fast.
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel as PydanticModel

    from orchestrator.master import MasterOrchestrator

    # Create the FastAPI application instance.
    # title and version appear in the auto-generated /docs (Swagger UI) page.
    api = FastAPI(title="OpenStack AI Agent", version="0.1.0")

    # CORS (Cross-Origin Resource Sharing) middleware allows browser-based
    # frontends on a different domain/port to call this API.
    # allow_origins=["*"] accepts requests from any origin — safe for internal
    # tools but should be locked down to specific domains in production.
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   # Restrict to known frontend origins in production.
        allow_methods=["*"],   # Allow GET, POST, PUT, DELETE, etc.
        allow_headers=["*"],   # Allow all request headers (e.g. Authorization).
    )

    # Instantiate the orchestrator once and reuse it across all HTTP requests.
    # Creating a new orchestrator per request would be expensive (tool loading,
    # client initialisation) and would lose any in-memory session state.
    # The underscore prefix prevents FastAPI from treating this as a route
    # dependency when it is closed over inside the route functions below.
    _orchestrator = MasterOrchestrator()

    # Pydantic model that describes the JSON body expected by POST /chat.
    # FastAPI validates incoming requests against this schema automatically
    # and returns HTTP 422 if required fields are missing or have wrong types.
    class ChatRequest(PydanticModel):
        message: str                    # The natural-language request from the client.
        user_id: str = "anonymous"      # Caller identity; defaults to "anonymous" if omitted.
        project_id: Optional[str] = None   # OpenStack project scope; None = orchestrator default.
        session_id: Optional[str] = None   # Omit to start a new conversation; include to continue one.

    # ── POST /chat ────────────────────────────────────────────────────────────
    # Main endpoint: accepts a user message and returns the agent's response.
    # The full result dict from MasterOrchestrator is returned as JSON,
    # including final_response, session_id, success flag, and any tool outputs.
    @api.post("/chat")
    async def chat(req: ChatRequest):
        """Send a message to the agent and receive a structured response."""
        result = await _orchestrator.handle(
            message=req.message,
            user_id=req.user_id,
            project_id=req.project_id,
            session_id=req.session_id,
        )
        return result

    # ── GET /health ───────────────────────────────────────────────────────────
    # Liveness probe endpoint used by Kubernetes, Docker Compose health checks,
    # and load balancers to verify the process is alive and accepting traffic.
    # Returns HTTP 200 with {"status": "ok"} when the server is healthy.
    @api.get("/health")
    async def health():
        """Liveness probe — used by load balancers and container orchestrators."""
        return {"status": "ok"}

    console.print(f"[cyan]Starting API server on http://{host}:{port}[/cyan]")

    # uvicorn.run() is a blocking call — it starts its own asyncio event loop
    # and runs until the process is killed.  Control never returns past this line
    # during normal operation.
    uvicorn.run(api, host=host, port=port)


# ── Demo mode ─────────────────────────────────────────────────────────────────

async def _run_demo():
    """
    Run a fixed set of demo prompts and print the agent's responses.

    Useful for smoke-testing the full pipeline end-to-end without needing an
    interactive terminal (e.g. in CI pipelines or recorded screencasts).
    Each prompt exercises a different agent capability so the full system
    (VM management, monitoring, diagnostics, recommendations) is covered.
    """
    # Deferred import — same pattern as _run_cli; only loaded when needed.
    from orchestrator.master import MasterOrchestrator

    orchestrator = MasterOrchestrator()

    # Predefined list of (user_id, project_id, message) tuples.
    # Each entry represents one independent user request.
    # All share the same user ("alice") and project ("proj-demo") so the
    # orchestrator can apply consistent scoping across all demo calls.
    # The messages are ordered to cover: listing → creation → monitoring →
    # diagnostics → recommendations, matching common operator workflows.
    demo_messages = [
        ("alice", "proj-demo", "List all my running instances"),
        ("alice", "proj-demo", "Create a VM called web-server-01 with 2 vCPUs and 4GB RAM"),
        ("alice", "proj-demo", "What is the current CPU usage of the cluster?"),
        ("alice", "proj-demo", "Why is instance abc-123 in ERROR state?"),
        ("alice", "proj-demo", "Give me performance recommendations for my project"),
    ]

    # Print a header panel so the output is clearly labelled when captured in
    # logs or a terminal recording.
    console.print(Panel.fit("[bold]OpenStack AI Agent — Demo Mode[/bold]", border_style="cyan"))

    # Iterate through each demo prompt sequentially (not in parallel) so the
    # output is readable and the order matches the list above.
    # Note: session_id is intentionally omitted from each call so every message
    # is treated as the start of a new conversation — outputs stay independent
    # and self-contained, making them easy to compare individually.
    for user_id, project_id, message in demo_messages:
        console.print(f"\n[bold green]User:[/bold green] {message}")

        # Show a spinner while the orchestrator processes the request.
        with console.status("[dim]Processing…[/dim]"):
            result = await orchestrator.handle(
                message=message, user_id=user_id, project_id=project_id
                # session_id omitted → new independent conversation each time
            )

        # Print a separator and render the response as Markdown.
        console.print(Rule("[dim]Agent response[/dim]", style="dim"))
        console.print(Markdown(result["final_response"]))


# ── CLI entry point ───────────────────────────────────────────────────────────
#
# main() is the single entry point for the entire application.
# Typer reads the function signature and auto-generates a fully documented
# CLI with --help, type validation, and default values — no manual argparse needed.
#
# Responsibilities:
#   1. Parse command-line arguments (mode, user, project, log level, host, port).
#   2. Initialise the logging stack before any other code runs.
#   3. Dispatch to the correct runtime mode:
#        cli    → _run_cli()    — blocking interactive REPL
#        server → _run_server() — blocking HTTP API server
#        demo   → _run_demo()   — non-interactive scripted run
#
# All three modes are blocking: the function only returns after the mode exits
# (user types "exit", server is killed, or demo finishes).

@app.command()
def main(
    # Selects which runtime mode to launch.
    # "cli"    → interactive terminal session (default, most common use).
    # "server" → start a FastAPI HTTP server (for UI or API integrations).
    # "demo"   → run a fixed set of scripted prompts (for testing or demos).
    mode: str = typer.Option("cli", "--mode", "-m", help="cli | server | demo"),

    # Identifies the operator making requests.  Passed to the orchestrator on
    # every turn for audit logging and any per-user quota/permission checks.
    # Defaults to "engineer" so local dev sessions don't need to set this.
    user_id: str = typer.Option("engineer", "--user", "-u", help="User ID"),

    # Scopes all OpenStack API calls to a specific tenant project.
    # If omitted (None), the orchestrator falls back to its configured default.
    # Useful when a single user manages multiple projects and wants to target one.
    project_id: Optional[str] = typer.Option(None, "--project", "-p", help="OpenStack project ID"),

    # Minimum log severity to print.  Controls verbosity at runtime without
    # changing code.  Use "DEBUG" to trace internal agent decisions; "ERROR" to
    # suppress everything except failures.  Defaults to "WARNING" to keep the
    # terminal output clean during normal operation.
    log_level: str = typer.Option("WARNING", "--log-level", "-l", help="Logging level"),

    # Network interface the HTTP server binds to (server mode only).
    # "0.0.0.0" listens on all interfaces — reachable from other machines.
    # Use "127.0.0.1" to restrict access to the local machine only.
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Server host (server mode only)"),

    # TCP port the HTTP server listens on (server mode only).
    # 8080 is the default; change if the port is already in use on your machine.
    port: int = typer.Option(8080, "--port", help="Server port (server mode only)"),
):
    """OpenStack AI Agent — multi-agent infrastructure management."""

    # Configure logging before anything else runs so that log records emitted
    # during module imports (e.g. orchestrator loading tools) are not lost.
    _configure_logging(log_level)

    if mode == "cli":
        # asyncio.run() creates a brand-new event loop, drives _run_cli to
        # completion, then shuts the loop down cleanly — the recommended way
        # to run a top-level async function from synchronous code in Python 3.7+.
        asyncio.run(_run_cli(user_id=user_id, project_id=project_id))

    elif mode == "server":
        # _run_server is a plain synchronous function because uvicorn creates
        # and manages its own event loop internally.  Do NOT wrap it in asyncio.run().
        _run_server(host=host, port=port)

    elif mode == "demo":
        # Same asyncio.run() pattern as CLI mode; demo is also async because
        # it awaits the orchestrator just like the interactive loop does.
        asyncio.run(_run_demo())

    else:
        # Any unrecognised --mode value is a user error; print a helpful message
        # and exit with a non-zero code so shell scripts can detect the failure.
        console.print(f"[red]Unknown mode: {mode}. Use cli | server | demo[/red]")
        raise typer.Exit(1)


# Allow running directly with `python main.py` in addition to the `typer` CLI
# entry point defined in pyproject.toml / setup.cfg.  Both paths call app().
if __name__ == "__main__":
    app()
