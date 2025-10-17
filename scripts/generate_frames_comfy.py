"""Stub utilities to interact with ComfyUI / AnimateDiff pipelines."""
from __future__ import annotations

import json
import os
import random
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import cv2
import numpy as np
from loguru import logger

from app.utils import build_job_directories, ensure_dir, load_config, persist_prompt, random_seed


def _simulate_frame(width: int, height: int, frame_index: int, total_frames: int) -> np.ndarray:
    """Generate a synthetic frame for offline development and tests."""
    logger.debug("Simulating frame {}/{}", frame_index + 1, total_frames)
    base = np.zeros((height, width, 3), dtype=np.uint8)
    gradient = np.linspace(0, 255, width, dtype=np.uint8)
    base[:, :, 0] = gradient
    base[:, :, 1] = np.roll(gradient, frame_index * 5)
    base[:, :, 2] = np.roll(gradient[::-1], frame_index * 3)
    noise = np.random.default_rng(frame_index).integers(0, 30, size=base.shape, dtype=np.uint8)
    return cv2.add(base, noise)


def _write_frame(path: Path, frame: np.ndarray) -> None:
    ensure_dir(path.parent)
    cv2.imwrite(str(path), frame)


def _generate_dummy_frames(job_id: str, frame_count: int, width: int, height: int) -> List[Path]:
    job_dirs = build_job_directories(job_id)
    frames_dir = job_dirs["frames"]
    frame_paths: List[Path] = []
    for index in range(frame_count):
        frame = _simulate_frame(width, height, index, frame_count)
        frame_path = frames_dir / f"frame_{index + 1:04d}.png"
        _write_frame(frame_path, frame)
        frame_paths.append(frame_path)
    logger.info("Generated {} dummy frames for job {}", len(frame_paths), job_id)
    return frame_paths


def call_comfyui_cli(scene_payload: Dict, job_id: str) -> List[Path]:
    """Invoke ComfyUI CLI if configured, fallback to dummy frames."""
    config = load_config()
    render_cfg = config.get("render", {})
    fps = int(render_cfg.get("fps", 30))
    duration = scene_payload.get("duration", 4)
    total_frames = fps * duration
    width = int(render_cfg.get("resolution", {}).get("width", 1080))
    height = int(render_cfg.get("resolution", {}).get("height", 1920))

    comfyui_cli = os.getenv("COMFYUI_CLI") or os.environ.get("COMFYUI_CLI")
    persist_prompt(scene_payload.get("scene_id", job_id), scene_payload)

    if not comfyui_cli:
        logger.warning("COMFYUI_CLI not configured. Falling back to dummy frame generation.")
        return _generate_dummy_frames(job_id, total_frames, width, height)

    command = [
        "python",
        comfyui_cli,
        "--workflow",
        json.dumps(scene_payload),
        "--model",
        config.get("comfyui", {}).get("default_model", "sdxl"),
        "--output",
        str(build_job_directories(job_id)["frames"]),
        "--seed",
        str(random_seed()),
    ]

    logger.info("Running ComfyUI CLI: {}", " ".join(command))
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        logger.error("ComfyUI CLI not found. Generating dummy frames instead.")
        return _generate_dummy_frames(job_id, total_frames, width, height)
    except subprocess.CalledProcessError as exc:
        logger.error("ComfyUI CLI failed (%s). Using dummy frames.", exc)
        return _generate_dummy_frames(job_id, total_frames, width, height)

    frames_dir = build_job_directories(job_id)["frames"]
    frame_paths = sorted(frames_dir.glob("*.png"))
    if not frame_paths:
        logger.warning("No frames returned by ComfyUI CLI. Generating dummy frames.")
        return _generate_dummy_frames(job_id, total_frames, width, height)

    return frame_paths


def generate_frames(scene_payload: Dict, job_id: str) -> List[Path]:
    """Public API to obtain frame paths for a scene."""
    return call_comfyui_cli(scene_payload, job_id)
