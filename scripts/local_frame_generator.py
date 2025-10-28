"""
Gerador de frames usando modelos locais (Stable Diffusion, ControlNet, AnimateDiff)
"""

import torch
import numpy as np
from PIL import Image
from typing import List, Optional, Dict, Any
import cv2
import logging
from model_manager import ModelManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalFrameGenerator:
    """Gera frames de animação usando modelos locais"""

    def __init__(self, config: Dict[str, Any], model_manager: ModelManager):
        """
        Inicializa gerador local

        Args:
            config: Configurações do projeto
            model_manager: Gerenciador de modelos
        """
        self.config = config
        self.model_manager = model_manager
        self.device = model_manager.device

        # Configurações de geração
        self.gen_config = config.get('local_models', {}).get('generation', {})

    def generate_variation_img2img(
        self,
        base_image: Image.Image,
        prompt: str,
        strength: float = 0.3,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 30
    ) -> Image.Image:
        """
        Gera variação usando Stable Diffusion img2img

        Args:
            base_image: Imagem base
            prompt: Prompt de geração
            strength: Força da transformação (0-1, menor = mais similar)
            guidance_scale: Guidance scale
            num_inference_steps: Número de steps

        Returns:
            Imagem gerada
        """
        logger.info("Gerando variação com SD img2img...")

        # Carregar pipeline
        pipeline = self.model_manager.load_stable_diffusion(use_img2img=True)

        # Preparar imagem
        # SD espera múltiplos de 64
        width, height = base_image.size
        new_width = (width // 64) * 64
        new_height = (height // 64) * 64

        if (new_width, new_height) != (width, height):
            base_image = base_image.resize((new_width, new_height), Image.LANCZOS)

        # Gerar
        result = pipeline(
            prompt=prompt,
            image=base_image,
            strength=strength,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            negative_prompt="blurry, low quality, distorted, deformed"
        ).images[0]

        # Restaurar tamanho original se necessário
        if (new_width, new_height) != (width, height):
            result = result.resize((width, height), Image.LANCZOS)

        return result

    def generate_with_controlnet(
        self,
        base_image: Image.Image,
        prompt: str,
        controlnet_type: str = "canny",
        controlnet_conditioning_scale: float = 0.8,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 30
    ) -> Image.Image:
        """
        Gera imagem usando ControlNet para máxima consistência

        Args:
            base_image: Imagem base
            prompt: Prompt
            controlnet_type: Tipo de ControlNet (canny, depth, etc)
            controlnet_conditioning_scale: Força do ControlNet
            guidance_scale: Guidance scale
            num_inference_steps: Número de steps

        Returns:
            Imagem gerada
        """
        logger.info(f"Gerando com ControlNet ({controlnet_type})...")

        # Carregar pipeline ControlNet
        pipeline = self.model_manager.load_controlnet(controlnet_type)

        # Preparar conditioning image baseado no tipo
        if controlnet_type == "canny":
            conditioning_image = self._prepare_canny(base_image)
        elif controlnet_type == "depth":
            conditioning_image = self._prepare_depth(base_image)
        else:
            conditioning_image = base_image

        # Ajustar tamanho
        width, height = base_image.size
        new_width = (width // 64) * 64
        new_height = (height // 64) * 64

        if (new_width, new_height) != (width, height):
            conditioning_image = conditioning_image.resize(
                (new_width, new_height),
                Image.LANCZOS
            )

        # Gerar
        result = pipeline(
            prompt=prompt,
            image=conditioning_image,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            controlnet_conditioning_scale=controlnet_conditioning_scale,
            negative_prompt="blurry, low quality, distorted, deformed"
        ).images[0]

        # Restaurar tamanho
        if (new_width, new_height) != (width, height):
            result = result.resize((width, height), Image.LANCZOS)

        return result

    def _prepare_canny(self, image: Image.Image, low_threshold: int = 100, high_threshold: int = 200) -> Image.Image:
        """Prepara imagem Canny para ControlNet"""
        img_array = np.array(image)

        # Converter para grayscale se necessário
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Aplicar Canny
        edges = cv2.Canny(gray, low_threshold, high_threshold)

        # Converter para RGB
        edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

        return Image.fromarray(edges_rgb)

    def _prepare_depth(self, image: Image.Image) -> Image.Image:
        """Prepara depth map (simplificado - idealmente usar MiDaS)"""
        # Esta é uma implementação simplificada
        # Para melhor qualidade, use MiDaS ou outro modelo de depth
        img_array = np.array(image)

        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Simular depth com blur e normalização
        depth = cv2.GaussianBlur(gray, (21, 21), 0)
        depth = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX)

        # Converter para RGB
        depth_rgb = cv2.cvtColor(depth, cv2.COLOR_GRAY2RGB)

        return Image.fromarray(depth_rgb)

    def generate_keyframes_sd(
        self,
        base_image: Image.Image,
        num_keyframes: int = 10,
        method: str = "img2img",
        base_prompt: str = None
    ) -> List[Image.Image]:
        """
        Gera keyframes usando Stable Diffusion

        Args:
            base_image: Imagem base
            num_keyframes: Número de keyframes
            method: Método (img2img ou controlnet)
            base_prompt: Prompt base

        Returns:
            Lista de keyframes
        """
        logger.info(f"Gerando {num_keyframes} keyframes com método: {method}")

        keyframes = [base_image]

        # Prompt base
        if base_prompt is None:
            base_prompt = self.config.get('local_models', {}).get('prompts', {}).get(
                'base',
                "cosmic scene, space explorer character, ethereal glow, stars, nebula"
            )

        # Variações de prompt
        variations = [
            "subtle floating particles",
            "enhanced cosmic glow",
            "twinkling stars background",
            "gentle hair and cloth movement",
            "ethereal lighting effects",
            "soft nebula clouds",
            "cosmic dust particles",
            "glowing aura effect"
        ]

        # Strength progression (começar suave, aumentar gradualmente)
        strengths = np.linspace(0.2, 0.4, num_keyframes - 1)

        for i in range(1, num_keyframes):
            # Selecionar variação
            variation = variations[i % len(variations)]
            full_prompt = f"{base_prompt}, {variation}"

            strength = float(strengths[i - 1])

            try:
                if method == "controlnet":
                    new_frame = self.generate_with_controlnet(
                        base_image=keyframes[-1],
                        prompt=full_prompt,
                        controlnet_type="canny",
                        controlnet_conditioning_scale=0.8
                    )
                else:  # img2img
                    new_frame = self.generate_variation_img2img(
                        base_image=keyframes[-1],
                        prompt=full_prompt,
                        strength=strength,
                        guidance_scale=7.5
                    )

                keyframes.append(new_frame)
                logger.info(f"Keyframe {i}/{num_keyframes-1} gerado")

            except Exception as e:
                logger.error(f"Erro ao gerar keyframe {i}: {e}")
                # Fallback: duplicar último frame
                keyframes.append(keyframes[-1].copy())

        return keyframes

    def generate_with_animatediff(
        self,
        base_image: Image.Image,
        prompt: str,
        num_frames: int = 16,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 25
    ) -> List[Image.Image]:
        """
        Gera sequência de frames com AnimateDiff

        Args:
            base_image: Imagem base (será usada como referência)
            prompt: Prompt de animação
            num_frames: Número de frames (múltiplo de 8)
            guidance_scale: Guidance scale
            num_inference_steps: Steps

        Returns:
            Lista de frames animados
        """
        logger.info(f"Gerando {num_frames} frames com AnimateDiff...")

        try:
            # Carregar pipeline
            pipeline = self.model_manager.load_animatediff()

            # Ajustar num_frames para múltiplo de 8
            num_frames = ((num_frames + 7) // 8) * 8

            # Gerar
            result = pipeline(
                prompt=prompt,
                negative_prompt="blurry, low quality, distorted",
                num_frames=num_frames,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                height=512,
                width=512
            )

            frames = result.frames[0]

            # Redimensionar para match com base_image se necessário
            target_size = base_image.size
            frames = [
                Image.fromarray(frame).resize(target_size, Image.LANCZOS)
                for frame in frames
            ]

            logger.info(f"AnimateDiff gerou {len(frames)} frames")
            return frames

        except Exception as e:
            logger.error(f"Erro com AnimateDiff: {e}")
            # Fallback
            logger.info("Usando fallback img2img")
            return self.generate_keyframes_sd(
                base_image,
                num_keyframes=num_frames // 5,
                method="img2img"
            )

    def batch_generate_variations(
        self,
        base_images: List[Image.Image],
        prompts: List[str],
        method: str = "img2img"
    ) -> List[Image.Image]:
        """
        Gera variações em batch

        Args:
            base_images: Lista de imagens base
            prompts: Lista de prompts
            method: Método de geração

        Returns:
            Lista de imagens geradas
        """
        logger.info(f"Geração em batch: {len(base_images)} imagens")

        results = []

        for i, (image, prompt) in enumerate(zip(base_images, prompts)):
            logger.info(f"Processando {i+1}/{len(base_images)}")

            if method == "controlnet":
                result = self.generate_with_controlnet(image, prompt)
            else:
                result = self.generate_variation_img2img(image, prompt)

            results.append(result)

        return results
