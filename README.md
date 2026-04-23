# OpenStack AI Agent System

A multi-agent AI system for managing OpenStack infrastructure through natural language — built on LangGraph and Claude.

---

## Architecture

```text
Master Orchestrator (LangGraph)
├── Customer Chatbot Agent      — Natural language VM / network / storage provisioning
├── Infra Management Agent      — IaC execution (Terraform / Ansible / OpenStack SDK)
├── RCA & Remediation Agent     — Root cause analysis and automated fixes
├── Monitoring & Actions Agent  — Prometheus + OpenSearch alerting and response
└── Performance & Advisory      — Trend analysis and optimisation recommendations
```

---

## Quick Start

### 1 — Clone and set up the environment

```bash
git clone <repo-url>
cd OpenStack_Agents

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2 — Configure credentials

```bash
cp config/.env.example config/.env
# Edit config/.env with your OpenStack credentials and Anthropic API key
```

### 3 — Run

**Option A — One command (backend + frontend together):**

```bash
./run.sh                         # backend :8080, frontend UI :5173
./run.sh --port 9090             # custom backend port
```

Press `Ctrl-C` once to stop both services cleanly.

**Option B — Backend only (CLI modes):**

```bash
# Interactive terminal chat
python main.py

# REST API server
python main.py --mode server --port 8080

# Scripted demo (5 pre-written prompts, no interaction needed)
python main.py --mode demo
```

**Option C — Frontend only (requires backend already running):**

```bash
cd frontend
npm install
npm run dev      # opens http://localhost:5173
```

---

## Modes

| Mode | How to run | Description |
| --- | --- | --- |
| `cli` | `python main.py` | Interactive REPL — type requests in natural language |
| `server` | `python main.py --mode server` | FastAPI REST API (`POST /chat`, `GET /health`) |
| `demo` | `python main.py --mode demo` | Runs 5 scripted prompts automatically, no input needed |
| UI | `./run.sh` | Vue 3 web interface for server + demo modes |

---

## Frontend UI

A Vue 3 + TypeScript + Tailwind CSS single-page app in [`frontend/`](frontend/).

**Chat tab** — Full conversational interface with:

- Markdown-rendered agent responses (code blocks, tables, lists)
- Session memory — all turns in one conversation thread
- "Approval required" and "Agent error" status badges
- Quick-start suggestion chips in the empty state

**Demo tab** — One-click demo runner with:

- Sequential execution of 5 scripted OpenStack prompts
- Per-card loading spinner and success / error indicators
- Completion banner with "Run Again" button

**Settings sidebar** — Configurable server URL, user ID, project ID, live connection test, and clear session.

---

## Project Structure

```text
OpenStack_Agents/
├── main.py                         # Entry point — CLI, server, and demo modes
├── run.sh                          # Dev launcher — starts backend + frontend together
├── requirements.txt
│
├── config/
│   ├── settings.py                 # Pydantic settings (reads from .env)
│   └── .env.example                # Template — copy to .env and fill in values
│
├── orchestrator/
│   └── master.py                   # Master Orchestrator — LangGraph graph definition
│
├── agents/
│   ├── base.py                     # BaseAgent — shared interface all agents inherit
│   ├── chatbot/agent.py            # Natural language provisioning
│   ├── infra/agent.py              # IaC execution
│   ├── rca/agent.py                # Root cause analysis
│   ├── monitoring/agent.py         # Alerting and automated response
│   └── performance/agent.py        # Trend analysis and recommendations
│
├── tools/
│   ├── openstack/
│   │   ├── nova.py                 # Compute  (instances, flavors, keypairs)
│   │   ├── neutron.py              # Networking (networks, subnets, routers)
│   │   ├── cinder.py               # Block storage (volumes, snapshots)
│   │   ├── keystone.py             # Identity (projects, users, tokens)
│   │   └── glance.py               # Images
│   ├── monitoring/
│   │   ├── prometheus.py           # Metrics queries (PromQL)
│   │   └── opensearch.py           # Log search (DSL queries)
│   └── iac/
│       ├── terraform.py            # Terraform plan / apply / destroy wrappers
│       └── ansible.py              # Ansible playbook execution
│
├── frontend/                       # Vue 3 web UI
│   ├── src/
│   │   ├── App.vue                 # Root layout (header + sidebar + tabs)
│   │   ├── components/
│   │   │   ├── AppHeader.vue       # Branding and connection status
│   │   │   ├── SettingsSidebar.vue # Server URL, user, project settings
│   │   │   ├── ChatMode.vue        # Interactive chat interface
│   │   │   ├── DemoMode.vue        # Scripted demo runner
│   │   │   └── MessageBubble.vue   # Individual chat bubble with Markdown
│   │   ├── composables/
│   │   │   ├── useChat.ts          # Chat state and session management
│   │   │   └── useDemo.ts          # Demo prompt queue and state
│   │   ├── api/client.ts           # Fetch wrappers for /chat and /health
│   │   └── types/index.ts          # TypeScript interfaces
│   ├── package.json
│   └── vite.config.ts
│
└── tests/
    ├── test_orchestrator.py
    └── test_tools.py
```

---

## API Reference

### `POST /chat`

Send a natural-language message to the agent.

**Request body:**

```json
{
  "message":    "List all my running instances",
  "user_id":    "engineer",
  "project_id": "my-project",       
  "session_id": "abc-123"           
}
```

> `project_id` and `session_id` are optional. Omit `session_id` to start a new conversation; include it to continue an existing thread.

**Response:**

```json
{
  "final_response":    "Here are your running instances…",
  "session_id":        "abc-123",
  "success":           true,
  "pending_approvals": []
}
```

### `GET /health`

Liveness probe. Returns `{"status": "ok"}` with HTTP 200 when the server is healthy.

---

## Safety Model

Every state-changing action passes through three gates before execution:

1. **Schema validation** — tool inputs are type-checked and range-validated
2. **Guardrail check** — destructive operations (delete, reboot, resize) require explicit user approval
3. **Audit log** — every action is recorded with user ID, timestamp, and result

---

## Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `OS_AUTH_URL` | Yes | Keystone endpoint |
| `OS_USERNAME` | Yes | OpenStack service account |
| `OS_PASSWORD` | Yes | Service account password |
| `OS_PROJECT_NAME` | Yes | Default project scope |
| `PROMETHEUS_URL` | No | Prometheus base URL |
| `OPENSEARCH_URL` | No | OpenSearch base URL |
| `VECTOR_DB_URL` | No | Qdrant / Weaviate endpoint for RAG |
| `AGENT_DRY_RUN` | No | Set `true` to disable all writes (safe mode) |
| `APPROVAL_REQUIRED` | No | Comma-separated list of actions requiring approval |

---

## Running Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```
