# backend/models.py
# DB models for storing plans and tasks.

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from .database import Base

class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True, index=True)
    goal_text = Column(String(512), nullable=False)
    created_by = Column(String(128), nullable=True)
    created_on = Column(String(32), nullable=True)  # stored as ISO date string for simplicity

    tasks = relationship("Task", back_populates="plan", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"))
    title = Column(String(256))
    description = Column(Text)
    start_date = Column(String(32), nullable=True)  # ISO date string for simplicity
    end_date = Column(String(32), nullable=True)
    depends_on = Column(String(256), nullable=True)  # CSV of task ids or titles

    plan = relationship("Plan", back_populates="tasks")
