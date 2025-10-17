"""FastAPI application entry point for ai_character_animator."""
from __future__ import annotations

import uuid
from typing import Dict

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.schemas import (
    GenerateResponse,
    JobStatus,
    RenderResponse,
    RunAllResponse,
    SceneRequest,
    StatusResponse,
)
from app.utils import build_job_directories, cleanup_job, load_config, slugify_scene
from scripts.generate_frames_comfy import generate_frames
from scripts.postprocess import apply_postprocess
from scripts.render_ffmpeg import RenderError, render_video

app = FastAPI(title="AI Character Animator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobStore:
    """In-memory job registry."""

    def __init__(self) -> None:
        self.jobs: Dict[str, Dict] = {}

    def create_job(self, scene: SceneRequest) -> str:
        base_id = slugify_scene(scene.scene_id) or "job"
        job_id = f"{base_id}-{uuid.uuid4().hex[:8]}"
        self.jobs[job_id] = {
            "status": JobStatus.QUEUED,
            "scene": scene.model_dump(),
            "frames": [],
            "video": None,
            "detail": None,
        }
        logger.info("Created job {} for scene {}", job_id, scene.scene_id)
        return job_id

    def update(self, job_id: str, **kwargs) -> None:
        if job_id not in self.jobs:
            raise KeyError(job_id)
        self.jobs[job_id].update(kwargs)

    def get(self, job_id: str) -> Dict:
        job = self.jobs.get(job_id)
        if not job:
            raise KeyError(job_id)
        return job


job_store = JobStore()


def get_job_store() -> JobStore:
    return job_store


@app.post("/generate", response_model=GenerateResponse)
async def generate(
    scene: SceneRequest,
    background_tasks: BackgroundTasks,
    store: JobStore = Depends(get_job_store),
) -> GenerateResponse:
    """Queue a generation job and run it asynchronously."""
    job_id = store.create_job(scene)
    store.update(job_id, status=JobStatus.RUNNING)

    def task() -> None:
        try:
            logger.info("Starting frame generation for job {}", job_id)
            frames = generate_frames(scene.model_dump(), job_id)
            processed_frames = apply_postprocess(job_id)
            frame_list = [str(path) for path in (processed_frames or frames)]
            store.update(
                job_id,
                status=JobStatus.COMPLETED,
                frames=frame_list,
                detail=f"Generated {len(frame_list)} frames",
            )
            logger.success("Job {} completed generation", job_id)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Job {} failed during generation", job_id)
            store.update(job_id, status=JobStatus.FAILED, detail=str(exc))

    background_tasks.add_task(task)

    return GenerateResponse(job_id=job_id, status=JobStatus.RUNNING)


@app.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str, store: JobStore = Depends(get_job_store)) -> StatusResponse:
    try:
        job = store.get(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc

    return StatusResponse(
        job_id=job_id,
        status=job["status"],
        detail=job.get("detail"),
        frames=job.get("frames"),
        video=job.get("video"),
    )


@app.post("/render/{job_id}", response_model=RenderResponse)
async def render(job_id: str, store: JobStore = Depends(get_job_store)) -> RenderResponse:
    try:
        job = store.get(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc

    if job.get("status") not in {JobStatus.COMPLETED, JobStatus.RUNNING}:
        raise HTTPException(status_code=400, detail="Job must have generated frames before rendering")

    try:
        video_path = render_video(job_id)
    except RenderError as exc:
        store.update(job_id, status=JobStatus.FAILED, detail=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    store.update(job_id, video=str(video_path))
    logger.success("Video rendered for job {}", job_id)
    return RenderResponse(job_id=job_id, output_video=str(video_path))


@app.post("/run_all", response_model=RunAllResponse)
async def run_all(scene: SceneRequest, store: JobStore = Depends(get_job_store)) -> RunAllResponse:
    job_id = store.create_job(scene)
    try:
        store.update(job_id, status=JobStatus.RUNNING)
        frames = generate_frames(scene.model_dump(), job_id)
        processed = apply_postprocess(job_id)
        frame_list = [str(p) for p in (processed or frames)]
        store.update(job_id, frames=frame_list)
        video_path = render_video(job_id)
        store.update(job_id, video=str(video_path), status=JobStatus.COMPLETED, detail="Run all completed")
        return RunAllResponse(job_id=job_id, output_video=str(video_path))
    except RenderError as exc:
        store.update(job_id, status=JobStatus.FAILED, detail=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pylint: disable=broad-except
        store.update(job_id, status=JobStatus.FAILED, detail=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.on_event("startup")
async def on_startup() -> None:
    config = load_config()
    paths = config.get("paths", {})
    if paths:
        build_job_directories("bootstrap")
        cleanup_job("bootstrap", keep_frames=False)
    logger.info("AI Character Animator API ready")
