"""Post-processing utilities for generated frames."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import cv2
import numpy as np
from loguru import logger

from app.utils import build_job_directories, ensure_dir, list_png_files, load_config


def _apply_color_grade(image: np.ndarray) -> np.ndarray:
    lut = np.linspace(0, 255, 256, dtype=np.uint8)
    lut = np.clip(lut * 1.05, 0, 255).astype(np.uint8)
    return cv2.LUT(image, lut)


def _apply_glow(image: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(image, (0, 0), sigmaX=8)
    return cv2.addWeighted(image, 0.7, blur, 0.3, 0)


def _apply_motion_blur(image: np.ndarray) -> np.ndarray:
    kernel_size = 15
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[int((kernel_size - 1) / 2), :] = np.ones(kernel_size)
    kernel /= kernel_size
    return cv2.filter2D(image, -1, kernel)


def _apply_film_grain(image: np.ndarray) -> np.ndarray:
    noise = np.random.normal(0, 12, image.shape).astype(np.float32)
    noisy = image.astype(np.float32) + noise
    return np.clip(noisy, 0, 255).astype(np.uint8)


def _apply_vignette(image: np.ndarray) -> np.ndarray:
    rows, cols = image.shape[:2]
    kernel_x = cv2.getGaussianKernel(cols, cols / 2)
    kernel_y = cv2.getGaussianKernel(rows, rows / 2)
    kernel = kernel_y * kernel_x.T
    mask = kernel / kernel.max()
    vignette = image * mask[..., None]
    return np.clip(vignette, 0, 255).astype(np.uint8)


def _apply_depth_pass(image: np.ndarray, depth_dir: Path, frame_name: str) -> np.ndarray:
    depth_dir.mkdir(parents=True, exist_ok=True)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    depth_map = cv2.GaussianBlur(gray, (21, 21), 0)
    depth_path = depth_dir / f"{frame_name}_depth.png"
    cv2.imwrite(str(depth_path), depth_map)
    return image


def apply_effects(frame_paths: Iterable[Path], job_id: str) -> List[Path]:
    config = load_config()
    render_cfg = config.get("render", {})
    effects_cfg = render_cfg.get("postprocess", {})
    job_dirs = build_job_directories(job_id)
    output_dir = ensure_dir(job_dirs["outputs"])
    depth_dir = ensure_dir(job_dirs["depth"])

    processed_paths: List[Path] = []
    for frame_path in frame_paths:
        frame = cv2.imread(str(frame_path))
        if frame is None:
            logger.warning("Skipping unreadable frame: {}", frame_path)
            continue

        frame_name = frame_path.stem
        if effects_cfg.get("color_grade", True):
            frame = _apply_color_grade(frame)
        if effects_cfg.get("glow", True):
            frame = _apply_glow(frame)
        if effects_cfg.get("motion_blur", False):
            frame = _apply_motion_blur(frame)
        if effects_cfg.get("film_grain", True):
            frame = _apply_film_grain(frame)
        if effects_cfg.get("vignette", False):
            frame = _apply_vignette(frame)
        if effects_cfg.get("depth_pass", False):
            _apply_depth_pass(frame, depth_dir, frame_name)

        output_frame_path = output_dir / f"{frame_name}.png"
        cv2.imwrite(str(output_frame_path), frame)
        processed_paths.append(output_frame_path)

    logger.info("Post-processed {} frames for job {}", len(processed_paths), job_id)
    return processed_paths


def apply_postprocess(job_id: str) -> List[Path]:
    job_dirs = build_job_directories(job_id)
    frame_paths = list_png_files(job_dirs["frames"])
    if not frame_paths:
        logger.warning("No frames found for job {} during post-process", job_id)
        return []
    return apply_effects(frame_paths, job_id)
