"""Pydantic schemas for ai_character_animator."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MotionType(str, Enum):
    LOOP = "loop"
    TAKE = "take"


class SceneTake(BaseModel):
    take_id: str = Field(..., description="Identifier for the take")
    prompt_override: Optional[str] = Field(
        None, description="Optional override for the base prompt"
    )
    duration: int = Field(..., ge=1, description="Duration of the take in seconds")
    motion_type: MotionType = Field(MotionType.TAKE)


class SceneRequest(BaseModel):
    scene_id: str = Field(..., description="Unique identifier for the scene")
    prompt_base: str = Field(..., description="Base prompt for generation")
    camera: str = Field(..., description="Camera directions")
    duration: int = Field(..., ge=1, description="Duration in seconds")
    motion_type: MotionType = Field(MotionType.TAKE)
    effects: List[str] = Field(default_factory=list, description="List of post effects")
    takes: List[SceneTake] = Field(default_factory=list, description="Optional take definitions")


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerateResponse(BaseModel):
    job_id: str
    status: JobStatus


class StatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    detail: Optional[str] = None
    frames: Optional[List[str]] = None
    video: Optional[str] = None


class RenderResponse(BaseModel):
    job_id: str
    output_video: str


class RunAllResponse(BaseModel):
    job_id: str
    output_video: str
