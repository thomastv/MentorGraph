# MentorGraph: GCP Quickstart, Auth & Deployment Guide

> **New to GCP?** This guide walks you through every service, how to create them in the console, how authentication works, and exactly how `agents-cli` connects to Artifact Registry and Cloud Storage during deployment.

---

## 1. GCP Services Used & What They Do

| Service | Category | What it does in MentorGraph |
| :--- | :--- | :--- |
| **Gemini Enterprise Agent Platform** | Agent Management | Unified control plane that registers, secures, monitors, and hosts the agent. Surfaces MentorGraph directly to managers inside their Gemini Enterprise workspace. |
| **Agent Runtime** | Compute | Serverless sandboxed environment that runs the `google-adk` workflow graph. Handles auto-scaling and fast cold starts — no servers to manage. |
| **BigQuery** | Data & Analytics | Stores employee directories, performance ratings, skills gaps, and internal LMS course enrolment history. Queried by the `internal_analyst_agent` at runtime. |
| **Artifact Registry** | Container Management | Managed Docker repository that stores the containerised image of the agent code after Cloud Build packages it. Agent Runtime pulls from here. |
| **Cloud Build** | CI/CD | Picks up source code staged in Cloud Storage, installs dependencies from `pyproject.toml`, and builds a container image pushed to Artifact Registry. |
| **Cloud Storage (GCS)** | Storage | Staging area. `agents-cli` uploads your source bundle here before Cloud Build picks it up. Also used for Terraform state and observability telemetry. |
| **IAM & Service Accounts** | Security | Controls which identities can access which services. `agents-cli infra` creates a dedicated service account with minimum required roles for the Agent Runtime. |

---

## 2. Console Provisioning Guide (Step-by-Step)

### Step A — Create a GCP Project
1. Open [console.cloud.google.com](https://console.cloud.google.com).
2. Click the **Project Selector** dropdown (top-left) → **New Project**.
3. Enter a project name (e.g. `mentorgraph-enterprise`) and note the auto-generated **Project ID** — this is what goes into `GOOGLE_CLOUD_PROJECT` in `.env` and `project` in `pyproject.toml`.
4. Link a billing account to activate the project.

---

### Step B — Enable Required APIs
1. In the search bar type **APIs & Services** → click **Library**.
2. Search for and click **Enable** on each of these:

| API | Service Name |
| :--- | :--- |
| Gemini Enterprise Agent Platform | `agentplatform.googleapis.com` |
| Vertex AI | `aiplatform.googleapis.com` |
| Cloud Build | `cloudbuild.googleapis.com` |
| Artifact Registry | `artifactregistry.googleapis.com` |
| Cloud Storage | `storage.googleapis.com` |
| BigQuery | `bigquery.googleapis.com` |
| IAM | `iam.googleapis.com` |

> **Tip:** `agents-cli infra single-project` will also enable any of these that are missing automatically, but it's good practice to enable them manually first so you understand what your project uses.

---

### Step C — Create the BigQuery Dataset
1. Search for **BigQuery** → click into the SQL Workspace.
2. In the Explorer pane, click the **⋮** menu next to your Project ID → **Create dataset**.
3. Set **Dataset ID** to `hr_dataset` (matches the default in `config.py`).
4. Set **Location** to `us-central1` (match your deployment region).
5. Click **Create Dataset**.
6. Optionally seed the tables with mock employee data:
   ```powershell
   uv run python -m hr_remediation_agent.setup_mock_bq
   ```

> **Note:** You do **not** need to manually create Artifact Registry repos or Cloud Storage buckets. `agents-cli infra` creates both automatically — see Section 4.

---

## 3. Authentication

For any GCP client library (BigQuery, Gemini, Cloud Build, etc.) to work, it needs to know **who you are**. There are two ways to provide credentials.

### Method 1 — Application Default Credentials (ADC) ✅ Recommended

This is the modern secure approach. No JSON key files are downloaded or stored — credentials live in your secure OS user profile, automatically refreshed.

```powershell
# 1. Install the gcloud CLI from https://cloud.google.com/sdk/docs/install
#    then open a new PowerShell terminal and run:

# 2. Log in with your Google account
gcloud auth login

# 3. Pin the CLI to your project
gcloud config set project your-gcp-enterprise-project

# 4. Generate Application Default Credentials (what Python client libs use)
gcloud auth application-default login
```

That's it. Every Python library (`google-cloud-bigquery`, `google-adk`, `agents-cli`) will **automatically** find and use these credentials. Leave `GOOGLE_APPLICATION_CREDENTIALS` blank in your `.env` file.

---

### Method 2 — Service Account JSON Key (CI/CD / automation)

Use this when running in a headless environment like GitHub Actions that can't do browser-based login.

1. Search for **IAM & Admin** → **Service Accounts** → **+ Create Service Account**.
2. Name it `mentorgraph-runtime-sa` and grant these roles:
   - `roles/agentplatform.admin`
   - `roles/aiplatform.admin`
   - `roles/bigquery.admin`
   - `roles/artifactregistry.writer`
   - `roles/cloudbuild.builds.editor`
   - `roles/storage.admin`
3. Click **Done** → open the new service account → **Keys** tab → **Add Key** → **JSON**.
4. Save the downloaded file somewhere **outside** this repository.
5. Set the path in your `.env`:
   ```env
   GOOGLE_APPLICATION_CREDENTIALS=C:\secure-keys\mentorgraph-sa.json
   ```

> [!CAUTION]
> Never commit the JSON key file to Git. It grants full programmatic access to your GCP project. The `.gitignore` in this repo already excludes `*.json.key` and `*-credentials.json` patterns.

---

## 4. How `agents-cli` Connects to Artifact Registry & Cloud Storage

This is the most important section to read before running any deployment command. The `agents-cli deploy` command **has no `--registry` or `--bucket` flags**. Instead it uses a two-layer design:

```
┌──────────────────────────────────────────────────────────────────────────┐
│              HOW agents-cli FINDS AND USES YOUR RESOURCES                │
│                                                                          │
│  ┌─────────────────────────────────┐                                     │
│  │  gcloud auth application-       │  ← Your identity. Every agents-cli  │
│  │  default login                  │    command inherits this token       │
│  │  (ADC on your machine)          │    automatically. No passwords.      │
│  └────────────────┬────────────────┘                                     │
│                   │                                                      │
│                   ▼                                                      │
│  ┌─────────────────────────────────┐                                     │
│  │  pyproject.toml                 │  ← Your coordinates. agents-cli      │
│  │  [tool.agents-cli]              │    derives the Artifact Registry     │
│  │    project  = "your-project"    │    path and GCS bucket name from     │
│  │    region   = "us-central1"     │    these values. No flags needed.    │
│  │    deployment_target = ...      │                                      │
│  └────────────────┬────────────────┘                                     │
│                   │                                                      │
│          ┌────────┴────────┐                                             │
│          ▼                 ▼                                             │
│  agents-cli infra    agents-cli deploy                                   │
│  (run once)          (run on each release)                               │
│  ┌────────────┐      ┌────────────────────────────────────────────────┐  │
│  │ Creates:   │      │ 1. Bundles source → uploads to GCS bucket     │  │
│  │ • AR repo  │      │ 2. Cloud Build picks up bundle from GCS       │  │
│  │ • GCS      │      │ 3. Builds Docker image, pushes to AR repo     │  │
│  │   bucket   │      │ 4. Agent Runtime pulls image from AR          │  │
│  │ • SA + IAM │      │ 5. Returns a live resource endpoint           │  │
│  └────────────┘      └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

**The two mechanisms in plain English:**

- **ADC (auth)** — When you run `gcloud auth application-default login`, a token is cached on your machine. Every `agents-cli` command, Cloud Build job, and Python GCP client picks up that token automatically from a well-known path. You never pass credentials as arguments.

- **`pyproject.toml` `[tool.agents-cli]` (config)** — The CLI reads `project` and `region` from this block and derives resource names from them. For example, with `project = "mentorgraph-prod"` and `region = "us-central1"`, it targets `us-central1-docker.pkg.dev/mentorgraph-prod/agents` for Artifact Registry and `gs://mentorgraph-prod-agents-staging` for Cloud Storage.

---

## 5. Deployment Walkthrough (Full Sequence)

> [!IMPORTANT]
> Run these commands **in order**. `infra` must succeed before `deploy`, because `deploy` needs the Artifact Registry repo and GCS bucket that `infra` creates.

### Step 1 — Configure `pyproject.toml`

Open [pyproject.toml](./pyproject.toml) and fill in your real project ID in the `[tool.agents-cli]` section:

```toml
[tool.agents-cli]
deployment_target = "agent_runtime"
project           = "your-gcp-enterprise-project"   # ← change this
region            = "us-central1"
app_name          = "HR_Remediation_Manager_App"
entry_point       = "hr_remediation_agent.deploy_gemini:app"
```

---

### Step 2 — Provision Infrastructure (once per project)

```powershell
uv run agents-cli infra single-project
```

This reads your `[tool.agents-cli]` block and your ADC credentials, then creates:

| Resource created | Example name |
| :--- | :--- |
| Artifact Registry Docker repo | `us-central1-docker.pkg.dev/your-project/agents` |
| Cloud Storage staging bucket | `gs://your-project-agents-staging` |
| Agent Runtime service account | `mentorgraph-runtime-sa@your-project.iam.gserviceaccount.com` |
| IAM bindings | Minimum roles for Agent Runtime to pull images and write logs |

After `infra` completes, authorize your local Docker client to push to Artifact Registry:

```powershell
gcloud auth configure-docker us-central1-docker.pkg.dev
```

---

### Step 3 — Build & Deploy (run on each release)

```powershell
uv run agents-cli deploy
```

No flags needed — all coordinates come from `pyproject.toml`. Use `--dry-run` to preview the underlying `gcloud` commands first without executing anything:

```powershell
uv run agents-cli deploy --dry-run
```

Deployment stages:

| # | Stage | What happens |
| :--- | :--- | :--- |
| 1 | Source staging | Source files zipped and uploaded to the GCS bucket |
| 2 | Container build | Cloud Build installs `pyproject.toml` deps and builds a Docker image |
| 3 | Registry push | Image pushed to the Artifact Registry repo |
| 4 | Runtime boot | Agent Runtime pulls the image and starts the `deploy_gemini:app` entry point |
| 5 | Endpoint issued | A resource path is returned, e.g. `projects/.../reasoningEngines/123` |

---

### Step 4 — Publish to Gemini Enterprise

```powershell
uv run agents-cli publish
```

Or manually via the console:
1. GCP Console → **Gemini Enterprise** → **Agent Studio**.
2. **Custom Agent Applications** → **Create App** → **Connect Custom Code Base**.
3. Paste your resource endpoint (printed at the end of `agents-cli deploy`).
4. Enable **Human In the Loop Approvals** in the app settings.

Department managers can now trigger MentorGraph directly from their Gemini Enterprise chat. The workflow runs parallel data miners, synthesises a tailored 60-day development plan, pauses at the HITL manager gate for edits, and outputs the final corporate email.
