# file: agent.py
from google.adk import Agent, Workflow
from hr_remediation_agent.data_tools import query_internal_hr_db, fetch_market_course_recommendations

# -------------------------------------------------------------
# 1. SPECIALIZED SUB-AGENTS (Executed Concurrently)
# -------------------------------------------------------------
internal_analyst_agent = Agent(
    name="internal_analyst",
    model="gemini-2.5-flash",
    instruction="""You are a data analyst sub-agent specializing in internal enterprise employee metrics.
    Given an employee ID, use your `query_internal_hr_db` tool to retrieve their historical performance,
    skills gap, department role, and internal LMS course completion status.
    Return only raw factual data trends, metric summaries, and enrollment logs found. Do not synthesize recommendations yet.""",
    tools=[query_internal_hr_db]
)

external_market_agent = Agent(
    name="external_market_matcher",
    model="gemini-2.5-flash",
    instruction="""You discover external training and education options. Identify the skills gap mentioned by 
    the team lead and call your tool `fetch_market_course_recommendations` to find relevant external courses.
    Present highly rated external course recommendations from trusted platforms.""",
    tools=[fetch_market_course_recommendations]
)

# -------------------------------------------------------------
# 2. STRATEGIC & COMMUNICATION AGENTS (Downstream Execution)
# -------------------------------------------------------------
strategy_agent = Agent(
    name="performance_strategist",
    model="gemini-2.5-pro", # Using Pro for advanced logic synthesis
    instruction="""You are an expert Human Resources Business Partner (HRBP) and Talent Development Strategist.
    Analyze the compiled data from internal analyst reports (BigQuery results) and external course recommendations (LMS matches).
    Synthesize this information into a tailored, highly actionable 60-day Performance Improvement Plan (PIP) / Development Strategy.
    Structure the strategy clearly:
    1. Executive Summary & Context (Who, what role, current performance assessment)
    2. Identified Skill & Performance Gaps
    3. Action Plan (Weeks 1-4, Weeks 5-8): Include internal courses to retry/complete and external materials to join.
    4. Key Progress Milestones and Success Criteria.
    Keep the tone professional, objective, supportive, and constructive."""
)

comms_agent = Agent(
    name="hr_communicator",
    model="gemini-2.5-flash",
    instruction="""You are a corporate communications specialist specializing in HR and manager-to-employee relations.
    Take the approved PIP/Development Strategy document and draft a highly supportive, professional, and compliant 
    email script that a team manager can send directly to the employee.
    The communication must:
    - Frame the development plan as a growth opportunity and investment in the employee's career.
    - Set clear expectations for regular syncs (e.g., bi-weekly).
    - Maintain a warm, clear, encouraging, yet professional and structured corporate tone.
    - Exclude internal HR metadata but keep all specific course names and targets intact."""
)

# -------------------------------------------------------------
# 3. WORKFLOW TOPOLOGY DEFINITION (Graph Assembly)
# -------------------------------------------------------------
# ADK 2.0 uses deterministic graph topologies via edge parameters.
# Placing multiple elements in a branch generates native asynchronous execution (Fan-out).
root_agent = Workflow(
    name="hr_remediation_workflow",
    edges=[
        # START fires both lookup agents in parallel
        ("START", internal_analyst_agent),
        ("START", external_market_agent),
        
        # Gathering metrics from both streams (Fan-in) into the strategist
        (internal_analyst_agent, strategy_agent),
        (external_market_agent, strategy_agent),
        
        # Transitioning the strategist output directly to the communications writer
        # The Human-in-the-Loop gate is handled by the Agent Platform runtime settings
        (strategy_agent, comms_agent)
    ]
)
