# OpenStack AI Agent System

A multi-agent AI system for managing OpenStack infrastructure — built on LangGraph.

## Architecture

```bash
Master Orchestrator
├── Customer Chatbot Agent     — Natural language VM/network/storage provisioning
├── Infra Management Agent     — IaC execution (Terraform / Ansible / OpenStack SDK)
├── RCA & Remediation Agent    — Root cause analysis and auto-fix
├── Monitoring & Actions Agent — Prometheus + OpenSearch alerting and response
└── Performance & Advisory     — Trend analysis and optimization recommendations
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp config/.env.example config/.env
# Edit config/.env with your OpenStack credentials and API keys

# Run the agent (interactive CLI)
python main.py

# Run as API server
python main.py --mode server --port 8080
```

## Project Structure

```bash
openstack-ai-agent/
├── main.py                        # Entry point (CLI + server)
├── requirements.txt
├── config/
│   ├── settings.py                # Pydantic settings (reads from .env)
│   └── .env.example
├── orchestrator/
│   ├── __init__.py
│   ├── master.py                  # Master Orchestrator (LangGraph graph)
│   ├── router.py                  # Intent classification + agent routing
│   └── guardrails.py              # Action safety checks + approval gates
├── agents/
│   ├── base.py                    # BaseAgent class all agents inherit
│   ├── chatbot/
│   │   ├── __init__.py
│   │   └── agent.py               # Customer Chatbot Agent
│   ├── infra/
│   │   ├── __init__.py
│   │   └── agent.py               # Infrastructure Management Agent
│   ├── rca/
│   │   ├── __init__.py
│   │   └── agent.py               # Root Cause Analysis Agent
│   ├── monitoring/
│   │   ├── __init__.py
│   │   └── agent.py               # Monitoring & Actions Agent
│   └── performance/
│       ├── __init__.py
│       └── agent.py               # Performance & Advisory Agent
├── tools/
│   ├── openstack/
│   │   ├── nova.py                # Compute (instances, flavors, keypairs)
│   │   ├── neutron.py             # Networking (networks, subnets, routers)
│   │   ├── cinder.py              # Block storage (volumes, snapshots)
│   │   ├── keystone.py            # Identity (projects, users, tokens)
│   │   └── glance.py              # Images
│   ├── monitoring/
│   │   ├── prometheus.py          # Metrics queries (PromQL)
│   │   └── opensearch.py          # Log search (DSL queries)
│   └── iac/
│       ├── terraform.py           # Terraform plan/apply/destroy wrappers
│       └── ansible.py             # Ansible playbook execution
├── memory/
│   ├── __init__.py
│   ├── vector_store.py            # Vector DB (RAG over docs + runbooks)
│   ├── session.py                 # Per-user session memory
│   └── state_cache.py             # Infra topology snapshot cache
└── tests/
    ├── test_orchestrator.py
    ├── test_tools.py
    └── test_agents.py
```

## Safety Model

Every state-changing action goes through three gates:

1. **Schema validation** — tool inputs are validated before execution
2. **Guardrail check** — destructive operations require explicit approval
3. **Audit log** — every action is logged with user, timestamp, and result

## Environment Variables

| Variable | Description |
| --- | --- |
| `OS_AUTH_URL` | Keystone endpoint |
| `OS_USERNAME` | OpenStack service account |
| `OS_PASSWORD` | Service account password |
| `OS_PROJECT_NAME` | Default project |
| `ANTHROPIC_API_KEY` | Claude API key |
| `PROMETHEUS_URL` | Prometheus base URL |
| `OPENSEARCH_URL` | OpenSearch base URL |
| `VECTOR_DB_URL` | Qdrant/Weaviate endpoint |
| `AGENT_DRY_RUN` | `true` to disable all writes (safe mode) |
| `APPROVAL_REQUIRED` | Comma-separated list of actions requiring human approval |
