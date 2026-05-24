# file: deploy_gemini.py
import os
from google.adk.apps import App
from hr_remediation_agent import config
from hr_remediation_agent.agent import root_agent

# ==============================================================================
# GEMINI ENTERPRISE DEPLOYMENT PACKAGING
# ==============================================================================
# The google-adk App class serves as the official deployment wrapper to build,
# containerize, and host your workflow on the Gemini Enterprise Agent Runtime.
# Under the hood, this sets up the conversation state, events logs, and tracing.

app = App(
    name="hr_remediation_workflow",
    root_agent=root_agent
)

# Debug helper to check that the app is initialized correctly
if __name__ == "__main__":
    print("=" * 70)
    print(" MENTORGRAPH GEMINI ENTERPRISE PACKAGING VERIFICATION ")
    print("=" * 70)
    print(f"App Target Name:      {app.name}")
    print(f"Root Workflow Node:   {app.root_agent.name}")
    print(f"Configured Region:    {config.LOCATION}")
    print(f"Target GCP Project:   {config.GCP_PROJECT_ID}")
    print("-" * 70)
    print("\n[OK] ADK App successfully compiled and validated locally.")
    print("This file acts as your entry point for production deployments.")
    print("To trigger deployment, please refer to the deployment guide below.")
    print("=" * 70)

# ==============================================================================
# GEMINI ENTERPRISE DEPLOYMENT INSTRUCTIONS
# ==============================================================================
#
# STEP 1: Enable the required APIs in your GCP Console
# --------------------------------------------------
# Enable the following Google Cloud APIs:
# - agentplatform.googleapis.com   (Gemini Enterprise Agent Platform API)
# - aiplatform.googleapis.com      (Vertex AI / Core Model Support)
# - cloudbuild.googleapis.com      (To build your agent sandbox containers)
# - artifactregistry.googleapis.com (To host your packaged agent images)
# - storage.googleapis.com         (To stage files during deployment)
# - bigquery.googleapis.com        (For BQ database query execution)
#
# STEP 2: Configure Service Account Roles
# ---------------------------------------
# Your deployment service account requires these roles:
# - Gemini Agent Platform Admin (roles/agentplatform.admin)
# - Vertex AI Administrator (roles/aiplatform.admin)
# - Storage Admin (roles/storage.admin)
# - Artifact Registry Writer (roles/artifactregistry.writer)
# - Cloud Build Editor (roles/cloudbuild.builds.editor)
#
# STEP 3: Deploy via the Google Agents CLI (agents-cli)
# -----------------------------------------------------
# The Agents CLI handles the packaging of the Adk App, containerizes the 
# dependencies from pyproject.toml, and registers it to the Agent Runtime.
#
# Command:
#   agents-cli deploy \
#     --project=your-gcp-enterprise-project \
#     --location=us-central1 \
#     --entry-point=hr_remediation_agent.deploy_gemini:app \
#     --display-name="HR_Remediation_Manager_App"
#
