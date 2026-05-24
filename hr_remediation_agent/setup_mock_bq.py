import sys
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from hr_remediation_agent import config

def setup_mock_dataset():
    """Provisions a mock BigQuery dataset and populates it with sample L&D metrics."""
    print("Initializing Google Cloud BigQuery Client...")
    try:
        # Initializing client. This will use credentials found in environment 
        # or via application-default credentials.
        client = bigquery.Client(project=config.GCP_PROJECT_ID)
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize BigQuery client: {e}")
        print("Please ensure GOOGLE_APPLICATION_CREDENTIALS or active gcloud auth credentials are set.")
        sys.exit(1)

    print(f"Checking if dataset '{config.BQ_DATASET_NAME}' exists in project '{config.GCP_PROJECT_ID}'...")
    dataset_ref = client.dataset(config.BQ_DATASET_NAME)
    
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset '{config.BQ_DATASET_NAME}' already exists.")
    except NotFound:
        print(f"Dataset '{config.BQ_DATASET_NAME}' not found. Creating dataset...")
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"  # Adjust location if needed
        try:
            client.create_dataset(dataset)
            print(f"Dataset '{config.BQ_DATASET_NAME}' created successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to create dataset: {e}")
            sys.exit(1)

    # 1. Employees Table Schema & Creation
    employees_table_id = config.EMPLOYEES_TABLE
    employees_schema = [
        bigquery.SchemaField("employee_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("department", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("role", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("performance_rating", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("skills_gap", "STRING", mode="NULLABLE"),
    ]
    
    # 2. Courses Table Schema & Creation
    courses_table_id = config.COURSES_TABLE
    courses_schema = [
        bigquery.SchemaField("course_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("course_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("provider", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("rating", "FLOAT", mode="REQUIRED"),
    ]
    
    # 3. Course Enrollments Table Schema & Creation
    enrollments_table_id = config.ENROLLMENTS_TABLE
    enrollments_schema = [
        bigquery.SchemaField("enrollment_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("employee_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("course_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("completion_time_days", "INTEGER", mode="NULLABLE"),
    ]

    def recreate_table(table_id, schema):
        table_ref = bigquery.Table(table_id, schema=schema)
        try:
            client.delete_table(table_id, not_found_ok=True)
            table = client.create_table(table_ref)
            print(f"Table '{table_id}' created successfully.")
            return table
        except Exception as e:
            print(f"[ERROR] Failed to create table '{table_id}': {e}")
            sys.exit(1)

    print("\nCreating/recreating table structures...")
    recreate_table(employees_table_id, employees_schema)
    recreate_table(courses_table_id, courses_schema)
    recreate_table(enrollments_table_id, enrollments_schema)

    # Insert mock records
    print("\nInserting sample records into tables...")
    
    employees_data = [
        {
            "employee_id": "EMP001",
            "name": "Jane Doe",
            "department": "Engineering",
            "role": "Senior Backend Engineer",
            "performance_rating": "Needs Improvement",
            "skills_gap": "Python Concurrency, System Design, Memory Management"
        },
        {
            "employee_id": "EMP002",
            "name": "John Smith",
            "department": "Product Management",
            "role": "Lead Product Manager",
            "performance_rating": "Meets Expectations",
            "skills_gap": "Strategic Communication, Technical Architecture Basics"
        },
        {
            "employee_id": "EMP003",
            "name": "Alice Johnson",
            "department": "Engineering",
            "role": "Software Engineer II",
            "performance_rating": "Exceeds Expectations",
            "skills_gap": "Kubernetes Orchestration"
        }
    ]

    courses_data = [
        {
            "course_id": "CRS001",
            "course_name": "Intro to Python Concurrency & Asyncio",
            "provider": "Internal L&D Portal",
            "rating": 4.2
        },
        {
            "course_id": "CRS002",
            "course_name": "Distributed System Design Fundamentals",
            "provider": "Internal L&D Portal",
            "rating": 4.7
        },
        {
            "course_id": "CRS003",
            "course_name": "Strategic Communication & Stakeholder Alignment",
            "provider": "Internal L&D Portal",
            "rating": 4.5
        },
        {
            "course_id": "CRS004",
            "course_name": "Kubernetes in Production",
            "provider": "Internal L&D Portal",
            "rating": 4.8
        }
    ]

    enrollments_data = [
        # Jane Doe (Failed concurrency, Lagging on system design)
        {
            "enrollment_id": "ENR001",
            "employee_id": "EMP001",
            "course_id": "CRS001",
            "status": "Failed",
            "completion_time_days": None
        },
        {
            "enrollment_id": "ENR002",
            "employee_id": "EMP001",
            "course_id": "CRS002",
            "status": "In Progress",
            "completion_time_days": 42
        },
        # John Smith
        {
            "enrollment_id": "ENR003",
            "employee_id": "EMP002",
            "course_id": "CRS003",
            "status": "Completed",
            "completion_time_days": 14
        },
        # Alice Johnson
        {
            "enrollment_id": "ENR004",
            "employee_id": "EMP003",
            "course_id": "CRS004",
            "status": "Completed",
            "completion_time_days": 8
        }
    ]

    try:
        # Employees insert
        errors = client.insert_rows_json(employees_table_id, employees_data)
        if errors:
            print(f"[ERROR] Inserting employees: {errors}")
        else:
            print("Successfully loaded 'employees' sample records.")

        # Courses insert
        errors = client.insert_rows_json(courses_table_id, courses_data)
        if errors:
            print(f"[ERROR] Inserting courses: {errors}")
        else:
            print("Successfully loaded 'courses' sample records.")

        # Enrollments insert
        errors = client.insert_rows_json(enrollments_table_id, enrollments_data)
        if errors:
            print(f"[ERROR] Inserting enrollments: {errors}")
        else:
            print("Successfully loaded 'course_enrollments' sample records.")
            
        print("\n" + "=" * 60)
        print(" MOCK BIGQUERY DATASET SETUP SUCCESSFULLY COMPLETED! ")
        print(" You can now run the agent.py using your GCP project! ")
        print("=" * 60)

    except Exception as e:
        print(f"[ERROR] Failed to load data into BigQuery tables: {e}")

if __name__ == "__main__":
    setup_mock_dataset()
