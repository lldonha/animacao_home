"""Utility helpers for ai_character_animator."""
from __future__ import annotations

import json
import os
import random
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml
from loguru import logger
from slugify import slugify

BASE_DIR = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def load_config(path: str | Path | None = None) -> Dict[str, Any]:
    """Load YAML configuration for the pipeline."""
    config_path = Path(path) if path else BASE_DIR / "config" / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def build_job_directories(job_id: str) -> Dict[str, Path]:
    config = load_config()
    paths = config.get("paths", {})
    base_frames = ensure_dir(BASE_DIR / paths.get("frames", "assets/frames"))
    base_outputs = ensure_dir(BASE_DIR / paths.get("outputs", "assets/outputs"))
    base_depth = ensure_dir(BASE_DIR / paths.get("depth", "assets/depth"))

    job_frames = ensure_dir(base_frames / job_id)
    job_outputs = ensure_dir(base_outputs / job_id)
    job_depth = ensure_dir(base_depth / job_id)

    return {
        "frames": job_frames,
        "outputs": job_outputs,
        "depth": job_depth,
    }


def slugify_scene(scene_id: str) -> str:
    return slugify(scene_id)


def random_seed() -> int:
    return random.randint(0, 2**32 - 1)


def persist_prompt(scene_id: str, payload: Dict[str, Any]) -> Path:
    config = load_config()
    prompts_dir = ensure_dir(BASE_DIR / config.get("paths", {}).get("prompts", "assets/prompts"))
    file_path = prompts_dir / f"{slugify_scene(scene_id)}.json"
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    logger.debug("Saved prompt payload to {}", file_path)
    return file_path


def cleanup_job(job_id: str, keep_frames: bool = True) -> None:
    config = load_config()
    paths = config.get("paths", {})
    base_frames = Path(BASE_DIR / paths.get("frames", "assets/frames"))
    base_outputs = Path(BASE_DIR / paths.get("outputs", "assets/outputs"))
    base_depth = Path(BASE_DIR / paths.get("depth", "assets/depth"))

    if base_outputs.exists():
        shutil.rmtree(base_outputs / job_id, ignore_errors=True)
    if base_depth.exists():
        shutil.rmtree(base_depth / job_id, ignore_errors=True)
    if not keep_frames and base_frames.exists():
        shutil.rmtree(base_frames / job_id, ignore_errors=True)


def list_png_files(directory: Path) -> List[Path]:
    return sorted([p for p in directory.glob("*.png") if p.is_file()])


def flatten(items: Iterable[Iterable[Any]]) -> List[Any]:
    return [element for iterable in items for element in iterable]
