# backend/task_logic.py
"""
Task decomposition + timeline engine.
Design goals:
- Work without an API key (has a mock LLM fallback).
- If OPENAI_API_KEY is present, call OpenAI completion for enhanced reasoning.
- Keep outputs deterministic enough for unit tests.
"""

from datetime import datetime, timedelta
import os
import re
import json
from typing import List, Dict, Any
import httpx

OPENAI_KEY = os.getenv("OPENAI_API_KEY", None)

def parse_goal_duration(goal: str):
    """
    Try to infer a target duration from the goal string.
    Returns duration in days (int) and a naive deadline (datetime) if found.
    """
    goal = goal.lower()
    now = datetime.utcnow()
    # common patterns
    m = re.search(r'(\d+)\s*(day|days|week|weeks|month|months)', goal)
    if m:
        num = int(m.group(1))
        unit = m.group(2)
        if 'week' in unit:
            days = num * 7
        elif 'month' in unit:
            days = num * 30
        else:
            days = num
        deadline = now + timedelta(days=days)
        return days, deadline
    # fallback: assume 14 days for short goals, else 30
    fallback = 14 if 'launch' in goal or 'ship' in goal or 'release' in goal else 30
    return fallback, now + timedelta(days=fallback)

def mock_llm_reasoning(goal_text: str) -> List[Dict[str, Any]]:
    """
    A small, heuristic 'LLM' that splits a goal into steps.
    This ensures the project runs without external keys.
    """
    # naive templates — intentionally simple and human-like
    title = goal_text.strip().capitalize()
    days, deadline = parse_goal_duration(goal_text)

    tasks = []

    # common phases for deliverable-type goals
    phases = [
        ("Define scope & success metrics", "Clarify goal, success metrics, target audience, and constraints."),
        ("Design & plan", "Create designs, wireframes or implementation plans."),
        ("Implementation", "Develop core functionality and integrate components."),
        ("Testing & QA", "Test features, fix bugs, and verify performance."),
        ("Deployment & Launch", "Deploy to production and run launch checklist."),
        ("Post-launch monitoring", "Monitor usage, collect feedback, and iterate.")
    ]

    # Keep number of tasks proportional to duration
    chosen = phases if days >= 10 else phases[:4]

    # Distribute timeline evenly across tasks
    per_task_days = max(1, days // len(chosen))
    start = datetime.utcnow()

    for i, (t, desc) in enumerate(chosen, start=1):
        s_date = (start + timedelta(days=(i-1)*per_task_days)).date().isoformat()
        e_date = (start + timedelta(days=i*per_task_days - 1)).date().isoformat()
        tasks.append({
            "title": t,
            "description": desc,
            "start_date": s_date,
            "end_date": e_date,
            "depends_on": "" if i == 1 else chosen[i-2][0]
        })

    # small heuristic additions based on keywords
    if "product" in goal_text.lower() and "marketing" in goal_text.lower():
        tasks.insert(len(tasks)-1, {
            "title": "Marketing prep",
            "description": "Prepare assets, landing page, email sequences and socials.",
            "start_date": (start + timedelta(days=per_task_days)).date().isoformat(),
            "end_date": (start + timedelta(days=per_task_days*2)).date().isoformat(),
            "depends_on": chosen[0][0]
        })
    return tasks

async def call_openai(prompt: str) -> str:
    """
    Minimal OpenAI call using the newer Chat completions via `gpt-3.5-turbo` style.
    This function is optional — if OPENAI_KEY not set, we won't call this.
    """
    if not OPENAI_KEY:
        raise RuntimeError("OpenAI key not configured.")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_KEY}"}
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are an assistant that breaks goals into task plans."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 800
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]

def build_prompt(goal: str) -> str:
    return (
        "Break down this user goal into an actionable task list. "
        "Include for each task: title, short description, estimated start date and end date (ISO YYYY-MM-DD), and dependencies (titles). "
        "If the goal includes a duration (e.g., 'in 2 weeks'), use that to set deadlines. "
        f"Goal: {goal}\n"
        "Return as JSON array of objects with keys: title, description, start_date, end_date, depends_on."
    )

async def generate_plan(goal_text: str, use_openai: bool = False):
    """
    Primary entry point for generating a plan.
    - If OpenAI key is available and use_openai True, use the API.
    - Otherwise fallback to the deterministic mock.
    """
    # quick hygiene
    goal_text = goal_text.strip()
    if use_openai and OPENAI_KEY:
        try:
            prompt = build_prompt(goal_text)
            reply = await call_openai(prompt)
            # try to parse JSON out of reply (many times the model will return JSON)
            try:
                parsed = json.loads(reply)
                # ensure keys exist
                return parsed
            except Exception:
                # fallback: return mock but include the raw reply as debug note
                plan = mock_llm_reasoning(goal_text)
                for t in plan:
                    t.setdefault("llm_note", reply[:400])
                return plan
        except Exception as e:
            # log (print for now) and fallback
            print("OpenAI call failed:", e)
            return mock_llm_reasoning(goal_text)
    else:
        return mock_llm_reasoning(goal_text)
