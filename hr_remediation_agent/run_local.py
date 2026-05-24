import os
import sys
import asyncio

# Resolve legacy Windows console encoding issues for Unicode outputs
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.status import Status
from rich.table import Table
from rich import print as rprint

# Ensure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hr_remediation_agent import config
from hr_remediation_agent.data_tools import query_internal_hr_db, fetch_market_course_recommendations

console = Console()

async def run_parallel_fetches(employee_id: str):
    """Executes the data-fetching sub-agents concurrently using asyncio.gather."""
    console.print("\n[bold cyan]> Step 1: Concurrently Triggering Parallel Data-Fetching Sub-agents...[/bold cyan]")
    
    # We will trigger the BQ internal fetch and external LMS fetch concurrently
    # This matches the fan-out behavior in the ADK graph topology
    with console.status("[bold yellow]Sub-agents running in parallel...[/bold yellow]") as status:
        # Define tasks
        loop = asyncio.get_event_loop()
        
        # BQ fetch is synchronous blocking, so run in executor to keep it async
        bq_task = loop.run_in_executor(None, query_internal_hr_db, employee_id)
        
        # LMS fetch is native async
        lms_task = fetch_market_course_recommendations("Python Concurrency, System Design") if employee_id == "EMP001" else \
                   fetch_market_course_recommendations("Strategic Communication") if employee_id == "EMP002" else \
                   fetch_market_course_recommendations("Kubernetes Orchestration")
        
        # Run concurrently
        bq_result, lms_result = await asyncio.gather(bq_task, lms_task)
        
    console.print("[bold green][OK] Both sub-agents finished execution successfully![/bold green]\n")
    
    # Display Internal analyst results
    bq_panel = Panel(
        bq_result,
        title="[bold yellow]Node 1A: Internal BigQuery Metrics (Factual DB Trends)[/bold yellow]",
        border_style="yellow"
    )
    console.print(bq_panel)
    
    # Display External market matcher results
    lms_panel = Panel(
        lms_result,
        title="[bold magenta]Node 1B: External LMS Catalog Recommendations[/bold magenta]",
        border_style="magenta"
    )
    console.print(lms_panel)
    
    return bq_result, lms_result

def simulate_strategy_synthesis(employee_id: str, bq_data: str, lms_data: str, custom_feedback: str = None) -> str:
    """Simulates the Gemini 2.5 Pro strategist node synthesizing the tailored PIP draft."""
    
    # Check if a real Gemini API Key is set in the environment to run actual live LLM synthesis
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            prompt = f"""
            You are the Performance Strategist Agent. Synthesize a 60-day Performance Improvement Plan (PIP) / Development Strategy
            based on the following gathered datasets.
            
            Internal Employee Metrics:
            {bq_data}
            
            External Course Catalog Matches:
            {lms_data}
            
            Additional Manager Feedback / Custom Instructions:
            {custom_feedback or "None"}
            
            Structure the response professionally with:
            1. Executive Summary & Context
            2. Identified Skill & Performance Gaps
            3. Action Plan (Weeks 1-4, Weeks 5-8) - highlight specific courses from the data
            4. Key Progress Milestones and Success Criteria.
            """
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt
            )
            return response.text
        except Exception as e:
            console.print(f"[yellow]Note: Real Gemini Call failed ({e}). Reverting to rich mock synthesis...[/yellow]")
            
    # Premium tailored Mock synthesis if offline or API key is not present
    modifier = f"\n[bold green]Manager Feedback Applied:[/bold green] {custom_feedback}" if custom_feedback else ""
    
    if employee_id == "EMP001":
        return f"""================================================================================
60-DAY EMPLOYEE DEVELOPMENT & REMEDIATION PLAN (Tailored for Jane Doe)
================================================================================
ROLE: Senior Backend Engineer (Engineering Department)
CURRENT PERFORMANCE RATING: Needs Improvement
TARGET SKILL GAPS: Python Concurrency, System Design, Memory Management
{modifier}

1. EXECUTIVE SUMMARY & CONTEXT:
Jane Doe is a talented Senior Backend Engineer who is currently struggling with core system throughput, 
asynchronous task queues, and large-scale architectural scaling. This has led to a "Needs Improvement" 
rating. This 60-day plan is structured to provide dedicated time, guidance, and training materials 
to help Jane build confidence and master these topics.

2. DETAILED ACTION PLAN:
* WEEKS 1-4: FOCUS ON CONCURRENCY & ASYNCIO MASTERY
  - Internal Retake: Enroll in and complete "Intro to Python Concurrency & Asyncio" (Internal L&D Portal - 4.2★).
  - External Core Resource: Complete "Advanced Python Architectures & Asynchronous Patterns" (Coursera - 4.9★).
  - Milestone: Complete a memory-safe asynchronous prototype of a high-throughput event worker.

* WEEKS 5-8: FOCUS ON DISTRIBUTED SYSTEMS ARCHITECTURE
  - Internal Support: Progress in "Distributed System Design Fundamentals" (Currently in progress for 42 days). Target completion by Week 6.
  - External Core Resource: Study "Pragmatic Distributed System Design at Hyper-Scale" (Educative - 4.9★).
  - Milestone: Participate in the architecture review of the upcoming billing queue refactor, presenting a technical design document.

3. SUCCESS CRITERIA & MEASUREMENT:
- Successful completion of both internal courses with positive supervisor assessment.
- Zero major thread pool starvation incidents in systems owned or deployed by Jane in staging environments.
- Active participation and high-quality design documentation delivered in week 6 architectural reviews.
"""
    elif employee_id == "EMP002":
        return f"""================================================================================
60-DAY L&D ALIGNMENT & GROWTH PLAN (Tailored for John Smith)
================================================================================
ROLE: Lead Product Manager (Product Management Department)
CURRENT PERFORMANCE RATING: Meets Expectations
TARGET SKILL GAPS: Strategic Communication, Technical Architecture Basics
{modifier}

1. EXECUTIVE SUMMARY & CONTEXT:
John Smith is a Lead Product Manager who consistently "Meets Expectations". To progress towards a Director role,
John needs to hone high-impact communication with executive leadership and gain a strong, high-level understanding
of system design principles to collaborate more effectively with principal engineers.

2. DETAILED ACTION PLAN:
* WEEKS 1-4: EXECUTIVE COMMUNICATION & ALIGNMENT
  - Action: Practice and integrate strategies from "Strategic Communication & Stakeholder Alignment" (Completed, 14 days).
  - External Course: Enroll in "Executive Presence & Strategic Communication for Tech Leaders" (LinkedIn Learning - 4.8★).
  - Milestone: Design and lead the monthly product roadmap review session for the VP of Product.

* WEEKS 5-8: TECHNICAL ARCHITECTURE FUNDAMENTALS
  - External Course: Take "High-Impact Technical Product Leadership" (Udemy - 4.6★).
  - Practical Task: Participate in technical refinement sessions for API design changes alongside Engineering Leads.
  - Milestone: Co-draft a product requirements document (PRD) detailing system scaling requirements.

3. SUCCESS CRITERIA & MEASUREMENT:
- Positive peer review from engineering leads on technical requirements clarity.
- Flawless, structured presentations in executive roadmap briefings.
"""
    else:
        return f"""================================================================================
60-DAY ADVANCED SKILL DEVELOPMENT TRACT (Tailored for {employee_id})
================================================================================
ROLE: Specialized Professional
CURRENT PERFORMANCE RATING: Meets Expectations
TARGET SKILLS: Cloud Native Infrastructure & Kubernetes Architecture
{modifier}

- Recommended Courses: Kubernetes Administrator (CKA) Production BootCamp (CloudAcademy - 4.9★)
- Primary Objective: Advance container orchestration skills to lead the core system migration.
- Milestone: Successful deployment of microservices to the new GKE cluster in sandbox environments.
"""

def simulate_comms_generation(pip_document: str) -> str:
    """Simulates the Gemini 2.5 Flash HR Comms agent generating the official email script."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            prompt = f"""
            You are the HR Communicator Agent. Take the following approved PIP document and generate a supportive,
            warm, yet structured and formal manager-to-employee email script.
            
            Approved Strategy Document:
            {pip_document}
            """
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text
        except Exception as e:
            pass

    # High quality mock response
    return f"""Subject: Supporting Your Growth: 60-Day Professional Development Plan

Dear Employee,

As part of our commitment to your continuous growth and success here at our enterprise, I have worked alongside our Talent Development team to put together a tailored 60-Day Professional Development Strategy for you.

We want to ensure you have the dedicated resources, support, and structured training necessary to excel. Over the next two months, we will be focusing on key developmental areas, including specific technical courses and milestone projects to support your mastery of these domains.

A draft of your tailored action plan is outlined below:
--------------------------------------------------------------------------------
{pip_document}
--------------------------------------------------------------------------------

We will schedule a brief sync every two weeks to discuss your progress, review any blockers, and ensure you have all the support you need. I am fully confident in your abilities, and I look forward to working together to help you achieve these milestones.

Best regards,

[Manager Name]
[Manager Title]
"""

async def main():
    # Print configuration header
    config.print_config()
    
    console.print("\n[bold green]Welcome to the MentorGraph Local CLI Sandbox Engine![/bold green]")
    console.print("This tool simulates the Google Cloud ADK execution graph in your terminal.\n")
    
    # 1. Trigger input
    employee_id = Prompt.ask(
        "[bold white]Enter Target Employee ID to initiate L&D review[/bold white]",
        choices=["EMP001", "EMP002", "EMP003"],
        default="EMP001"
    )
    
    # 2. Run data fetches (Fan-out)
    bq_data, lms_data = await run_parallel_fetches(employee_id)
    
    # 3. Strategist Node (Drafts Custom PIP)
    console.print("\n[bold cyan]> Step 2: Routing to Node 2: Performance Strategist (Synthesizing PIP)...[/bold cyan]")
    with console.status("[bold yellow]Synthesizing 60-day custom improvement strategy...[/bold yellow]"):
        pip_draft = simulate_strategy_synthesis(employee_id, bq_data, lms_data)
        await asyncio.sleep(1.0)
    
    # 4. Human-In-The-Loop Approval Gate (PAUSE AND EDIT)
    while True:
        console.print("\n" + "=" * 80)
        console.print("                  [bold yellow]*** HUMAN-IN-THE-LOOP (HITL) MANAGER GATE ***[/bold yellow]")
        console.print("=" * 80)
        console.print(Panel(pip_draft, title="[bold cyan]CURRENT Tailored 60-Day Development Plan Draft[/bold cyan]", border_style="cyan"))
        
        console.print("\n[bold white]What would you like to do as the Manager?[/bold white]")
        console.print("1. [bold green]Approve and Generate Official Communications[/bold green]")
        console.print("2. [bold yellow]Perform Live Text Edit (Manually overwrite or add text to the plan)[/bold yellow]")
        console.print("3. [bold magenta]Provide Feedback & Regenerate Strategy (Ask LLM to update its structure)[/bold magenta]")
        
        choice = Prompt.ask("Select an option", choices=["1", "2", "3"], default="1")
        
        if choice == "1":
            console.print("\n[bold green][OK] PIP Strategy Draft Approved by Manager! Proceeding to Comms Node...[/bold green]")
            break
        elif choice == "2":
            console.print("\n[bold yellow][EDIT] Enter text to APPEND/INSERT into the Action Plan Section:[/bold yellow]")
            live_edit = Prompt.ask("Manager Live Edits")
            pip_draft = pip_draft + f"\n\n[MANAGER LIVE OVERWRITE]: {live_edit}"
            console.print("[green][OK] Live edit saved successfully.[/green]")
        elif choice == "3":
            console.print("\n[bold magenta][FEEDBACK] Enter your custom feedback or guidance (e.g., 'Make it 90 days instead', 'Focus heavily on memory leaks'):[/bold magenta]")
            feedback = Prompt.ask("Manager Feedback")
            with console.status("[bold yellow]Regenerating strategy based on manager feedback...[/bold yellow]"):
                pip_draft = simulate_strategy_synthesis(employee_id, bq_data, lms_data, custom_feedback=feedback)
                await asyncio.sleep(1.0)
            console.print("[green][OK] Strategy regenerated successfully with feedback incorporated.[/green]")

    # 5. Node 3: HR Comms (Email Script Generation)
    console.print("\n[bold cyan]> Step 3: Routing to Node 3: HR Communicator (Drafting Corporate Email)...[/bold cyan]")
    with console.status("[bold yellow]Generating corporate-compliant support email...[/bold yellow]"):
        email_comms = simulate_comms_generation(pip_draft)
        await asyncio.sleep(1.0)
        
    console.print("\n" + "=" * 80)
    console.print("              [bold green]*** FINAL GENERATED CORPORATE COMMUNICATION ASSET ***[/bold green]")
    console.print("=" * 80)
    console.print(Panel(email_comms, title="[bold green]Official Manager-to-Employee Support Email[/bold green]", border_style="green"))
    console.print("\n[bold green][OK] Workflow completed successfully! The communication asset is ready to be sent.[/bold green]\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]Sandbox execution terminated by user.[/bold red]")
        sys.exit(0)
