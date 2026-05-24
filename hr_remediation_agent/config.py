import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists at the workspace root
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

# GCP Project Configuration
# Set these variables in your environment or a root .env file.
# E.g.
# GOOGLE_CLOUD_PROJECT=your-gcp-enterprise-project
# BQ_DATASET_NAME=hr_dataset
# GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

GCP_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-enterprise-project")
BQ_DATASET_NAME = os.getenv("BQ_DATASET_NAME", "hr_dataset")

# BigQuery Table Names
EMPLOYEES_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET_NAME}.employees"
ENROLLMENTS_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET_NAME}.course_enrollments"
COURSES_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET_NAME}.courses"

# Mock Settings for Local Sandbox Development
# Set to 'False' if you want to strictly enforce GCP service queries.
# If 'True', the agent will fallback to local mocks if BigQuery or LMS API is unreachable.
USE_MOCK_BQ = os.getenv("USE_MOCK_BQ", "True").lower() in ("true", "1", "yes")
USE_MOCK_LMS = os.getenv("USE_MOCK_LMS", "True").lower() in ("true", "1", "yes")

# Vertex AI Agent Engine Deployment Settings
LOCATION = os.getenv("GCP_LOCATION", "us-central1")
DEPLOYMENT_DISPLAY_NAME = os.getenv("DEPLOYMENT_DISPLAY_NAME", "HR_Remediation_Manager_App")

def print_config():
    """Debug helper to print current configuration values."""
    print("=" * 60)
    print(" MENTORGRAPH CONFIGURATION STATUS ")
    print("=" * 60)
    print(f"GCP Project ID:    {GCP_PROJECT_ID}")
    print(f"BigQuery Dataset:  {BQ_DATASET_NAME}")
    print(f"Employees Table:   {EMPLOYEES_TABLE}")
    print(f"Enrollments Table: {ENROLLMENTS_TABLE}")
    print(f"Courses Table:     {COURSES_TABLE}")
    print(f"Use Mock BQ:       {USE_MOCK_BQ} (Fallback mode)")
    print(f"Use Mock LMS:      {USE_MOCK_LMS} (Fallback mode)")
    print(f"Deployment Region: {LOCATION}")
    print("=" * 60)
