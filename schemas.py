# backend/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

class TaskOut(BaseModel):
    id: Optional[int]
    title: str
    description: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    depends_on: Optional[str]

class PlanCreate(BaseModel):
    goal_text: str = Field(..., example="Launch a product in 2 weeks")
    owner: Optional[str] = Field(None, example="Alice")

class PlanOut(BaseModel):
    id: Optional[int]
    goal_text: str
    created_by: Optional[str]
    created_on: Optional[str]
    tasks: List[TaskOut]
