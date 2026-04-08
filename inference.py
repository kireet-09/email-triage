"""
Inference script for email-triage-env.
Evaluates agent performance on tasks using OpenAI LLM.

Usage:
    python inference.py --task easy_triage
    python inference.py --task medium_categorize
    python inference.py --task hard_respond
    python inference.py --all
"""
import os
import sys
import json
import time
import argparse
import re
from typing import Dict, List, Optional
import requests
from openai import OpenAI


# ============================================================================
# Configuration from environment variables
# ============================================================================

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN", "")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")

# Validate HF_TOKEN
if not HF_TOKEN:
    print("Error: HF_TOKEN environment variable is required", file=sys.stderr)
    sys.exit(1)

# Initialize OpenAI client
client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)


# ============================================================================
# Logging utilities (strict JSON lines format)
# ============================================================================

def log_json(event_dict: dict):
    """Log a single JSON event to stdout."""
    print(json.dumps(event_dict))


def emit_start(task_id: str):
    """Emit [START] event."""
    log_json({
        "event": "[START]",
        "task_id": task_id,
        "model": MODEL_NAME,
        "env_url": ENV_BASE_URL,
        "timestamp": time.time()
    })


def emit_step(task_id: str, step: int, action: dict, reward: dict, done: bool, info: dict, cumulative_reward: float):
    """Emit [STEP] event."""
    log_json({
        "event": "[STEP]",
        "task_id": task_id,
        "step": step,
        "action": action,
        "reward": reward.get("value", 0.0),
        "done": done,
        "info": info,
        "cumulative_reward": cumulative_reward
    })


def emit_end(task_id: str, final_score: float, total_steps: int, cumulative_reward: float):
    """Emit [END] event."""
    log_json({
        "event": "[END]",
        "task_id": task_id,
        "final_score": final_score,
        "total_steps": total_steps,
        "cumulative_reward": cumulative_reward
    })


# ============================================================================
# Environment interaction
# ============================================================================

def reset_env(task_id: str) -> Dict:
    """Call POST /reset endpoint."""
    response = requests.post(
        f"{ENV_BASE_URL}/reset",
        json={"task_id": task_id}
    )
    response.raise_for_status()
    return response.json()


def step_env(action: dict) -> Dict:
    """Call POST /step endpoint."""
    response = requests.post(
        f"{ENV_BASE_URL}/step",
        json=action
    )
    response.raise_for_status()
    return response.json()


def get_state() -> Dict:
    """Call GET /state endpoint."""
    response = requests.get(f"{ENV_BASE_URL}/state")
    response.raise_for_status()
    return response.json()


# ============================================================================
# System prompts per task
# ============================================================================

SYSTEM_PROMPTS = {
    "easy_triage": """You are an email triage agent. Your job is to classify incoming business emails by priority level.

For each email, you MUST respond with ONLY a valid JSON object (no markdown, no extra text).

Instructions:
- Assign priority level: HIGH, MEDIUM, or LOW
- HIGH priority: urgent emails requiring immediate action or with significant business impact
- MEDIUM priority: important emails that need attention but are not immediately urgent
- LOW priority: low-impact emails, newsletters, casual communications

JSON format (REQUIRED):
{"action_type": "triage", "email_id": "<email_id>", "priority": "<HIGH|MEDIUM|LOW>"}

Examples of priority assignment:
- Production outage, critical security issue, contract expiration, angry customer → HIGH
- Performance reviews, budget questions → MEDIUM  
- Team lunch invite, newsletter, office supplies → LOW
""",
    
    "medium_categorize": """You are an email categorization agent. Your job is to classify business emails by priority AND department.

For each email, you MUST respond with ONLY a valid JSON object (no markdown, no extra text).

Instructions:
- Assign priority: HIGH (urgent, high impact), MEDIUM (important), LOW (low impact)
- Assign category: Support, Sales, HR, Legal, Finance, or Spam
- Support: customer issues, bugs, outages, service problems
- Sales: deals, partnerships, upsells, enterprise inquiries
- HR: hiring, PTO, performance, compensation, retention
- Legal: contracts, compliance, threats, data breaches
- Finance: invoices, payments, budgets, accounting
- Spam: newsletters, unsolicited, advertisements, phishing

JSON format (REQUIRED):
{"action_type": "categorize", "email_id": "<email_id>", "priority": "<HIGH|MEDIUM|LOW>", "category": "<Support|Sales|HR|Legal|Finance|Spam>"}
""",
    
    "hard_respond": """You are a comprehensive email triage and response agent. Your job is to classify emails AND draft responses for urgent issues.

For each email, you MUST respond with ONLY a valid JSON object (no markdown, no extra text).

Instructions:
1. For all emails: assign priority (HIGH/MEDIUM/LOW) and category (Support/Sales/HR/Legal/Finance/Spam)
2. For HIGH priority emails requiring substantive business response: draft a 40-80 word response
3. Response should be professional, specific to the problem, and actionable

Categories:
- Support: customer issues, outages, bugs, service problems
- Sales: deals, partnerships, enterprise inquiries
- HR: hiring, PTO, performance, compensation
- Legal: contracts, threats, data breaches
- Finance: invoices, payments, budgets
- Spam: newsletters, phishing, advertisements

For HIGH emails needing response, use:
{"action_type": "triage_and_respond", "email_id": "<email_id>", "priority": "HIGH", "category": "<category>", "response_draft": "<40-80 word response>"}

For other emails, use:
{"action_type": "categorize", "email_id": "<email_id>", "priority": "<MEDIUM|LOW>", "category": "<category>"}

Examples of emails needing response:
- Payment processing down, data breach, security vulnerability → needs urgent technical response
- Partnership proposal, enterprise deal → needs scheduling response
- Wrongful termination legal notice, data breach → needs legal acknowledgment

Examples not needing response:
- Office supplies restock, tax forms, low-impact requests → just categorize
"""
}


# ============================================================================
# LLM interaction
# ============================================================================

def build_user_prompt_easy(email: dict) -> str:
    """Build user prompt for easy_triage task."""
    return f"""Triage this email:

From: {email.get('from_', 'unknown')}
Subject: {email.get('subject', '(no subject)')}
Body: {email.get('body', '(no body)')}

Respond with ONLY valid JSON."""


def build_user_prompt_medium(email: dict) -> str:
    """Build user prompt for medium_categorize task."""
    return f"""Categorize this email:

From: {email.get('from_', 'unknown')}
Subject: {email.get('subject', '(no subject)')}
Body: {email.get('body', '(no body)')}

Respond with ONLY valid JSON."""


def build_user_prompt_hard(email: dict) -> str:
    """Build user prompt for hard_respond task."""
    return f"""Process this email:

From: {email.get('from_', 'unknown')}
Subject: {email.get('subject', '(no subject)')}
Body: {email.get('body', '(no body)')}

Respond with ONLY valid JSON. For HIGH priority emails that need a response, include a professional 40-80 word response draft."""


def call_llm(system_prompt: str, messages: List[Dict]) -> str:
    """Call OpenAI LLM and return response text."""
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=500,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error calling LLM: {e}", file=sys.stderr)
        return ""


def parse_action_json(response_text: str) -> Optional[dict]:
    """
    Parse JSON action from LLM response.
    Strips markdown code fences if present.
    """
    # Try to extract JSON from markdown code fences
    if "```" in response_text:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if match:
            response_text = match.group(1)
    
    try:
        action = json.loads(response_text)
        return action
    except json.JSONDecodeError:
        return None


# ============================================================================
# Task execution
# ============================================================================

def run_task(task_id: str) -> Dict:
    """
    Execute a complete task episode.
    
    Returns: {"task_id": str, "score": float, "steps": int, "cumulative_reward": float}
    """
    # Reset environment
    reset_result = reset_env(task_id)
    observation = reset_result.get("observation", {})
    inbox = observation.get("inbox", [])
    
    emit_start(task_id)
    
    # Get system prompt for task
    system_prompt = SYSTEM_PROMPTS.get(task_id, "")
    
    # Initialize conversation history
    messages = []
    
    cumulative_reward = 0.0
    step_count = 0
    
    # Process each email
    for email in inbox:
        # Build user prompt based on task
        if task_id == "easy_triage":
            user_prompt = build_user_prompt_easy(email)
        elif task_id == "medium_categorize":
            user_prompt = build_user_prompt_medium(email)
        else:  # hard_respond
            user_prompt = build_user_prompt_hard(email)
        
        # Add user message to history
        messages.append({"role": "user", "content": user_prompt})
        
        # Call LLM
        response_text = call_llm(system_prompt, messages)
        
        # Parse action
        action = parse_action_json(response_text)
        
        # Fallback if parsing fails
        if action is None:
            action = {"action_type": "triage", "email_id": email.get("id", ""), "priority": "MEDIUM"}
        
        # Ensure required fields
        if "email_id" not in action:
            action["email_id"] = email.get("id", "")
        if "action_type" not in action:
            action["action_type"] = "triage"
        
        # Add assistant message to history
        messages.append({"role": "assistant", "content": response_text})
        
        # Execute step
        step_result = step_env(action)
        
        reward = step_result.get("reward", {})
        done = step_result.get("done", False)
        info = step_result.get("info", {})
        
        step_count += 1
        cumulative_reward += reward.get("value", 0.0)
        
        # Emit step event
        emit_step(task_id, step_count, action, reward, done, info, cumulative_reward)
        
        if done:
            break
    
    # Get final state
    state = get_state()
    final_score = state.get("episode_score", 0.0)
    total_steps = state.get("current_step", step_count)
    cumulative_reward = state.get("cumulative_reward", cumulative_reward)
    
    # Emit end event
    emit_end(task_id, final_score, total_steps, cumulative_reward)
    
    return {
        "task_id": task_id,
        "score": final_score,
        "steps": total_steps,
        "cumulative_reward": cumulative_reward
    }


# ============================================================================
# Main CLI
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run email triage inference with LLM agent")
    parser.add_argument("--task", choices=["easy_triage", "medium_categorize", "hard_respond"],
                        help="Task to run")
    parser.add_argument("--all", action="store_true", help="Run all 3 tasks sequentially")
    
    args = parser.parse_args()
    
    tasks_to_run = []
    
    if args.all:
        tasks_to_run = ["easy_triage", "medium_categorize", "hard_respond"]
    elif args.task:
        tasks_to_run = [args.task]
    else:
        parser.print_help()
        sys.exit(1)
    
    results = []
    
    for task_id in tasks_to_run:
        try:
            result = run_task(task_id)
            results.append(result)
        except Exception as e:
            print(f"Error running task {task_id}: {e}", file=sys.stderr)
    
    # Emit summary table (as JSON for parsability)
    print("\n# SUMMARY", file=sys.stderr)
    print(json.dumps({"summary": results}, indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
