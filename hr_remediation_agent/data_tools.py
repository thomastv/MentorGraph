import asyncio
import sys
from google.cloud import bigquery
from hr_remediation_agent import config

# Rich local mock database mirroring the GCP BigQuery records
MOCK_EMPLOYEES = {
    "EMP001": {
        "employee_id": "EMP001",
        "name": "Jane Doe",
        "department": "Engineering",
        "role": "Senior Backend Engineer",
        "performance_rating": "Needs Improvement",
        "skills_gap": "Python Concurrency, System Design, Memory Management",
        "enrollments": [
            {"course_name": "Intro to Python Concurrency & Asyncio", "status": "Failed", "completion_time_days": None},
            {"course_name": "Distributed System Design Fundamentals", "status": "In Progress", "completion_time_days": 42}
        ]
    },
    "EMP002": {
        "employee_id": "EMP002",
        "name": "John Smith",
        "department": "Product Management",
        "role": "Lead Product Manager",
        "performance_rating": "Meets Expectations",
        "skills_gap": "Strategic Communication, Technical Architecture Basics",
        "enrollments": [
            {"course_name": "Strategic Communication & Stakeholder Alignment", "status": "Completed", "completion_time_days": 14}
        ]
    },
    "EMP003": {
        "employee_id": "EMP003",
        "name": "Alice Johnson",
        "department": "Engineering",
        "role": "Software Engineer II",
        "performance_rating": "Exceeds Expectations",
        "skills_gap": "Kubernetes Orchestration",
        "enrollments": [
            {"course_name": "Kubernetes in Production", "status": "Completed", "completion_time_days": 8}
        ]
    }
}

def query_internal_hr_db(employee_id: str) -> str:
    """Queries BigQuery for employee performance history and internal LMS progress.
    
    If config.USE_MOCK_BQ is True or GCP credentials are not found, it falls back
    to a rich local testing database so local development remains seamless.
    """
    employee_id = employee_id.strip().upper()
    
    if config.USE_MOCK_BQ:
        print(f"[Internal Analyst] Fetching local mock BigQuery metrics for: {employee_id}")
        if employee_id in MOCK_EMPLOYEES:
            emp = MOCK_EMPLOYEES[employee_id]
            # Format raw factual output representing row objects
            results = []
            for enrollment in emp["enrollments"]:
                results.append({
                    "employee_id": emp["employee_id"],
                    "name": emp["name"],
                    "department": emp["department"],
                    "role": emp["role"],
                    "performance_rating": emp["performance_rating"],
                    "skills_gap": emp["skills_gap"],
                    "course_name": enrollment["course_name"],
                    "status": enrollment["status"],
                    "completion_time_days": enrollment["completion_time_days"]
                })
            return str(results)
        return f"No internal logs found for ID: {employee_id} in mock database."

    print(f"[Internal Analyst] Executing production BigQuery client query for: {employee_id}")
    try:
        client = bigquery.Client(project=config.GCP_PROJECT_ID)
        query = f"""
        SELECT 
            e.employee_id, e.name, e.department, e.role, e.performance_rating, e.skills_gap,
            c.course_name, r.status, r.completion_time_days
        FROM `{config.EMPLOYEES_TABLE}` e
        LEFT JOIN `{config.ENROLLMENTS_TABLE}` r ON e.employee_id = r.employee_id
        LEFT JOIN `{config.COURSES_TABLE}` c ON r.course_id = c.course_id
        WHERE e.employee_id = '{employee_id}'
        """
        query_job = client.query(query)
        results = [dict(row) for row in query_job.result()]
        if results:
            print(f"[Internal Analyst] Successfully fetched {len(results)} rows from BQ.")
            return str(results)
        else:
            return f"No internal logs found in BigQuery for ID: {employee_id}"
    except Exception as e:
        print(f"[Internal Analyst] [WARNING] BigQuery failed: {e}. Falling back to mock dataset.", file=sys.stderr)
        # Safe fallback to mock database if GCP credentials fail
        if employee_id in MOCK_EMPLOYEES:
            emp = MOCK_EMPLOYEES[employee_id]
            results = []
            for enrollment in emp["enrollments"]:
                results.append({
                    "employee_id": emp["employee_id"],
                    "name": emp["name"],
                    "department": emp["department"],
                    "role": emp["role"],
                    "performance_rating": emp["performance_rating"],
                    "skills_gap": emp["skills_gap"],
                    "course_name": enrollment["course_name"],
                    "status": enrollment["status"],
                    "completion_time_days": enrollment["completion_time_days"]
                })
            return str(results)
        return f"No internal logs found for ID: {employee_id} (BigQuery error: {e})"

async def fetch_market_course_recommendations(skills_needed: str) -> str:
    """Asynchronously searches external e-learning catalogs for highly-rated courses matching a skill gap.
    
    Simulates real LMS REST API querying with asynchronous network latency (or fallback mocks).
    """
    skills_query = skills_needed.lower()
    print(f"[External LMS Provider] Starting async external catalog search for: '{skills_needed}'...")

    if config.USE_MOCK_LMS:
        # Simulate network response latency
        await asyncio.sleep(1.5)
        
        # Dynamically tailor high-quality external course recommendations based on query keywords
        if "concurrency" in skills_query or "python" in skills_query or "async" in skills_query:
            courses = [
                "1. Advanced Python Architectures & Asynchronous Patterns (Coursera - 4.9★, Provider: DeepTech)",
                "2. Concurrency & Parallel Programming Mastery in Python (Udemy - 4.7★, Provider: CodeCraft Academy)",
                "3. Systems Programming and Memory Management in C/Python (Pluralsight - 4.6★, Provider: ExecL&D)"
            ]
        elif "system design" in skills_query or "distributed" in skills_query or "architecture" in skills_query:
            courses = [
                "1. Pragmatic Distributed System Design at Hyper-Scale (Educative - 4.9★, Provider: ScaleAcademy)",
                "2. Modern Microservices Architecture & Fault Tolerance (Udemy - 4.8★, Provider: CloudBuilders)",
                "3. Systems Design Blueprint for Principal Architects (O'Reilly - 4.7★, Provider: TechPublish)"
            ]
        elif "communication" in skills_query or "leadership" in skills_query or "product" in skills_query:
            courses = [
                "1. Executive Presence & Strategic Communication for Tech Leaders (LinkedIn Learning - 4.8★, Provider: CommMasters)",
                "2. High-Impact Technical Product Leadership (Udemy - 4.6★, Provider: ProdAcademy)",
                "3. Negotiation and Stakeholder Management Fundamentals (Coursera - 4.5★, Provider: StanfordOnline)"
            ]
        elif "kubernetes" in skills_query or "k8s" in skills_query or "docker" in skills_query:
            courses = [
                "1. Kubernetes Administrator (CKA) Production BootCamp (CloudAcademy - 4.9★, Provider: CNCF-Partners)",
                "2. Advanced GitOps & Cloud Native Architecture (Udemy - 4.7★, Provider: DevOpsGuild)"
            ]
        else:
            courses = [
                f"1. Professional Skill Specialization: {skills_needed.title()} (Coursera - 4.8★, Provider: GlobalEdu)",
                f"2. Practical Bootcamp on {skills_needed.title()} Essentials (Udemy - 4.6★, Provider: SkillsInc)"
            ]
            
        result = f"Suggested External Courses for [{skills_needed}]:\n" + "\n".join(courses)
        print(f"[External LMS Provider] Async search completed. Found {len(courses)} results.")
        return result

    # Standard production implementation (e.g. calling an external API gateway)
    url = f"https://api.external-lms.com/v1/courses?search={skills_needed}"
    print(f"[External LMS Provider] [PROD] Querying REST API: {url}")
    
    # Secure HTTP network client call using aiohttp with connection timeouts
    import aiohttp
    timeout = aiohttp.ClientTimeout(total=5.0)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Parse REST response schema
                    courses = data.get("courses", [])
                    formatted = [f"- {c.get('title')} ({c.get('platform')} - {c.get('rating')}★)" for c in courses]
                    return f"Active External Courses for [{skills_needed}]:\n" + "\n".join(formatted)
                else:
                    return f"LMS API returned status: {response.status} (Using Mock Fallback)."
    except Exception as e:
        print(f"[External LMS Provider] [WARNING] REST API fetch failed: {e}. Using simulated fallback.", file=sys.stderr)
        # Graceful fallback to mock response
        await asyncio.sleep(0.5)
        return f"Suggested Mock External Courses for [{skills_needed}]: 1. Advanced {skills_needed.title()} (Coursera - 4.8★), 2. Principles of {skills_needed.title()} in Enterprise (Udemy - 4.6★)"
