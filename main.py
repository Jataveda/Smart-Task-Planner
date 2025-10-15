# backend/main.py
# FastAPI app to accept goal text and return structured plans.

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from .schemas import PlanCreate, PlanOut, TaskOut
from .database import engine, Base, get_db
from . import models
from .task_logic import generate_plan
from sqlalchemy.orm import Session
from datetime import datetime

# Create DB tables if they don't exist (simple dev approach)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Task Planner API", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to specific origin(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate-plan", response_model=PlanOut)
async def generate_plan_endpoint(payload: PlanCreate, db: Session = Depends(get_db)):
    """
    Accepts {goal_text, owner} and returns a plan. Plan is saved to DB.
    """
    if not payload.goal_text:
        raise HTTPException(status_code=400, detail="goal_text is required")

    # Ask task_logic to generate plan
    plan_items = await generate_plan(payload.goal_text, use_openai=False)  # default: no external API
    # plan_items is expected to be a list of dicts with keys: title, description, start_date, end_date, depends_on
    created_on = datetime.utcnow().isoformat()
    new_plan = models.Plan(goal_text=payload.goal_text, created_by=payload.owner, created_on=created_on)
    db.add(new_plan)
    db.flush()  # populate new_plan.id

    # Persist tasks
    for it in plan_items:
        t = models.Task(
            plan_id=new_plan.id,
            title=it.get("title", "Untitled Task"),
            description=it.get("description", ""),
            start_date=it.get("start_date"),
            end_date=it.get("end_date"),
            depends_on=str(it.get("depends_on", ""))
        )
        db.add(t)
    db.commit()
    db.refresh(new_plan)
    # prepare response
    tasks_out = [
        TaskOut(
            id=t.id, title=t.title, description=t.description,
            start_date=t.start_date, end_date=t.end_date, depends_on=t.depends_on
        ) for t in new_plan.tasks
    ]
    return PlanOut(
        id=new_plan.id,
        goal_text=new_plan.goal_text,
        created_by=new_plan.created_by,
        created_on=new_plan.created_on,
        tasks=tasks_out
    )

@app.get("/plans/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    tasks_out = [
        TaskOut(
            id=t.id, title=t.title, description=t.description,
            start_date=t.start_date, end_date=t.end_date, depends_on=t.depends_on
        ) for t in plan.tasks
    ]
    return PlanOut(
        id=plan.id,
        goal_text=plan.goal_text,
        created_by=plan.created_by,
        created_on=plan.created_on,
        tasks=tasks_out
    )

@app.get("/")
def root():
    return {"message": "Smart Task Planner API. POST /generate-plan to create a plan."}
