"""Utilities for compiling frames into final videos."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterable, List

from loguru import logger

from app.utils import build_job_directories, ensure_dir, list_png_files, load_config


class RenderError(RuntimeError):
    """Raised when ffmpeg fails to render the video."""


def build_ffmpeg_command(frames_pattern: str, output_path: Path, fps: int, crf: int, resolution: tuple[int, int]) -> List[str]:
    width, height = resolution
    return [
        os.getenv("FFMPEG_BIN", "ffmpeg"),
        "-y",
        "-framerate",
        str(fps),
        "-pattern_type",
        "glob",
        "-i",
        frames_pattern,
        "-vf",
        f"scale={width}:{height},format=yuv420p",
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]


def render_video(job_id: str, frames_dir: Path | None = None) -> Path:
    config = load_config()
    render_cfg = config.get("render", {})
    fps = int(render_cfg.get("fps", 30))
    crf = int(render_cfg.get("crf", 20))
    resolution_cfg = render_cfg.get("resolution", {})
    width = int(resolution_cfg.get("width", 1080))
    height = int(resolution_cfg.get("height", 1920))

    job_dirs = build_job_directories(job_id)
    frames_directory = frames_dir or job_dirs["outputs"]
    frames = list_png_files(frames_directory)
    if not frames:
        raise RenderError(f"No frames available in {frames_directory}")

    final_dir = ensure_dir(Path(config.get("paths", {}).get("final_renders", "final_renders")))
    output_path = final_dir / f"{job_id}.mp4"

    command = build_ffmpeg_command(
        str(frames_directory / "*.png"),
        output_path,
        fps,
        crf,
        (width, height),
    )

    logger.info("Running ffmpeg command: {}", " ".join(command))
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if process.returncode != 0:
        logger.error("FFmpeg error: {}", process.stderr)
        raise RenderError(process.stderr)

    logger.success("Rendered video for job {} at {}", job_id, output_path)
    return output_path
