# MentorGraph

**An intelligent, multi-node L&D Co-pilot built on the Google Cloud Agent Development Kit (ADK).**

MentorGraph helps enterprise managers design custom 60-day employee growth and remediation plans. When a skill gap or performance dip is identified, the agent concurrently queries internal HR metrics (BigQuery) and external course catalogs (LMS API), synthesises a tailored development plan, routes it through a Human-in-the-Loop approval gate for live manager edits, then automatically drafts the final corporate communication.

---

## Architecture

```
              [ Manager Input: Employee ID ]
                           │
                           ▼
               ┌───────────────────────┐
               │    Root Workflow      │   (google-adk Workflow graph)
               └───────────┬───────────┘
                           │  Fan-out (parallel)
          ┌────────────────┴────────────────┐
          ▼                                 ▼
┌──────────────────────┐       ┌──────────────────────┐
│  internal_analyst    │       │ external_market_     │
│  BigQuery metrics &  │       │ matcher              │
│  internal LMS data   │       │ External LMS catalog │
└──────────┬───────────┘       └──────────┬───────────┘
           │                              │
           └──────────────┬───────────────┘
                          │  Fan-in
                          ▼
               ┌───────────────────────┐
               │  performance_         │
               │  strategist           │   Gemini 2.5 Pro
               │  60-day PIP synthesis │
               └───────────┬───────────┘
                           │
                    ╔══════╧══════╗
                    ║  HITL GATE  ║  ← Workflow pauses for
                    ║  Manager    ║    manager review & edits
                    ║  Review     ║
                    ╚══════╤══════╝
                           │  (Approved)
                           ▼
               ┌───────────────────────┐
               │  hr_communicator      │   Gemini 2.5 Flash
               │  Drafts official      │
               │  support email        │
               └───────────────────────┘
```

---

## Project Structure

```
MentorGraph/
├── hr_remediation_agent/
│   ├── __init__.py          # Package init
│   ├── config.py            # GCP env variables & mock toggles
│   ├── data_tools.py        # BigQuery + async LMS API tools
│   ├── agent.py             # Agent definitions & Workflow graph
│   ├── deploy_gemini.py     # ADK App wrapper (deployment entry point)
│   ├── setup_mock_bq.py     # Seeds BigQuery with sample HR data
│   └── run_local.py         # Interactive CLI sandbox for local testing
├── .env.example             # Environment variable template (copy → .env)
├── .gitignore
├── DeploymentGuide.md       # Full GCP setup, auth & deployment walkthrough
├── pyproject.toml           # Dependencies + agents-cli deployment config
└── README.md
```

---

## Quick Start (Local Testing)

**Prerequisites:** Python 3.10+, [`uv`](https://docs.astral.sh/uv/)

```powershell
# 1. Clone and enter the repo
git clone https://github.com/your-org/MentorGraph
cd MentorGraph

# 2. Create virtual environment and install dependencies
uv venv
uv pip install -e .

# 3. Copy the environment template and fill in your values
Copy-Item .env.example .env

# 4. Run the interactive sandbox (uses mock data by default — no GCP needed)
uv run python -m hr_remediation_agent.run_local
```

The sandbox lets you select an employee (`EMP001`, `EMP002`, `EMP003`), watch the parallel sub-agents execute, review the synthesised strategy at the HITL gate, apply live edits or feedback, and see the final email output.

---

## Configuration

All configuration lives in `.env` (copy from `.env.example`):

| Variable | Purpose | Default |
| :--- | :--- | :--- |
| `GOOGLE_CLOUD_PROJECT` | Your GCP Project ID | `your-gcp-enterprise-project` |
| `BQ_DATASET_NAME` | BigQuery dataset name | `hr_dataset` |
| `GCP_LOCATION` | Deployment region | `us-central1` |
| `USE_MOCK_BQ` | Use local mock data instead of BigQuery | `True` |
| `USE_MOCK_LMS` | Use mock course catalog instead of live API | `True` |
| `GEMINI_API_KEY` | Optional — enables live Gemini model calls in `run_local.py` | _(blank)_ |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON key (leave blank if using ADC) | _(blank)_ |

---

## Seeding the BigQuery Mock Dataset

If you have GCP credentials configured, you can provision real BigQuery tables with sample employees:

```powershell
uv run python -m hr_remediation_agent.setup_mock_bq
```

This creates `hr_dataset.employees`, `hr_dataset.courses`, and `hr_dataset.course_enrollments` in your project with three sample employees across Engineering and Product Management.

---

## Deployment to Gemini Enterprise

Deployment uses [`agents-cli`](https://github.com/google/agents-cli) and follows a mandatory two-step sequence. See **[DeploymentGuide.md](./DeploymentGuide.md)** for the complete walkthrough including:

- Which GCP APIs to enable
- How to authenticate with ADC (recommended) or a Service Account key
- How `agents-cli` discovers Artifact Registry and Cloud Storage automatically
- The `agents-cli infra` → `agents-cli deploy` → `agents-cli publish` sequence

**TL;DR (after GCP is configured):**

```powershell
# 1. Provision infrastructure (once)
uv run agents-cli infra single-project

# 2. Authorize Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# 3. Build & deploy
uv run agents-cli deploy

# 4. Register in Gemini Enterprise workspace
uv run agents-cli publish
```

---

## Key Dependencies

| Package | Version | Purpose |
| :--- | :--- | :--- |
| `google-adk` | ≥ 2.0.0 | Agent orchestration framework |
| `google-cloud-bigquery` | ≥ 3.10.0 | Internal HR data queries |
| `aiohttp` | ≥ 3.8.0 | Async external LMS API calls |
| `python-dotenv` | ≥ 1.0.0 | `.env` file loading |
| `rich` | ≥ 13.0.0 | CLI formatting in `run_local.py` |
