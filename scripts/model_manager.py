"""
Gerenciador de modelos locais Hugging Face
"""

import os
import torch
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    StableDiffusionImg2ImgPipeline,
    ControlNetModel,
    StableDiffusionControlNetPipeline,
    AnimateDiffPipeline,
    DDIMScheduler,
    DPMSolverMultistepScheduler
)
from diffusers.utils import load_image
import gc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelManager:
    """Gerencia carregamento e uso de modelos locais Hugging Face"""

    def __init__(self, models_dir: str = "models", device: str = "cuda"):
        """
        Inicializa gerenciador de modelos

        Args:
            models_dir: Diretório raiz dos modelos
            device: Dispositivo (cuda ou cpu)
        """
        self.models_dir = Path(models_dir)
        self.device = device if torch.cuda.is_available() else "cpu"

        # Cache de modelos carregados
        self.loaded_models: Dict[str, Any] = {}

        # Detectar modelos disponíveis
        self.available_models = self._detect_available_models()

        logger.info(f"ModelManager inicializado no device: {self.device}")
        logger.info(f"Modelos disponíveis: {list(self.available_models.keys())}")

    def _detect_available_models(self) -> Dict[str, Path]:
        """Detecta modelos disponíveis no diretório"""
        available = {}

        # Procurar por modelos Stable Diffusion
        sd_paths = [
            self.models_dir / "stable_diffusion",
            Path.home() / ".cache/huggingface/hub",
            Path("/models/stable_diffusion")  # ComfyUI style
        ]

        for sd_path in sd_paths:
            if sd_path.exists():
                for model_dir in sd_path.iterdir():
                    if model_dir.is_dir():
                        # Verificar se tem arquivos de modelo
                        if self._is_valid_model_dir(model_dir):
                            model_name = model_dir.name
                            available[model_name] = model_dir
                            logger.info(f"Modelo detectado: {model_name}")

        return available

    def _is_valid_model_dir(self, path: Path) -> bool:
        """Verifica se diretório contém um modelo válido"""
        required_files = [
            "model_index.json",
            "unet/config.json",
            "vae/config.json"
        ]

        for req_file in required_files:
            if not (path / req_file).exists():
                return False

        return True

    def load_stable_diffusion(
        self,
        model_name: Optional[str] = None,
        variant: str = "fp16",
        use_img2img: bool = True
    ) -> Any:
        """
        Carrega modelo Stable Diffusion

        Args:
            model_name: Nome do modelo (None = auto-detect)
            variant: Variante (fp16 ou fp32)
            use_img2img: Usar pipeline img2img

        Returns:
            Pipeline carregado
        """
        cache_key = f"sd_{model_name}_{variant}_{use_img2img}"

        if cache_key in self.loaded_models:
            logger.info(f"Usando modelo em cache: {cache_key}")
            return self.loaded_models[cache_key]

        # Auto-detect modelo se não especificado
        if model_name is None:
            # Priorizar modelos SDXL
            for name in self.available_models:
                if "xl" in name.lower():
                    model_name = name
                    break

            # Fallback para qualquer SD
            if model_name is None and self.available_models:
                model_name = list(self.available_models.keys())[0]

        if model_name not in self.available_models:
            logger.error(f"Modelo {model_name} não encontrado")
            # Tentar carregar do Hub como fallback
            return self._load_from_hub(model_name, use_img2img)

        model_path = self.available_models[model_name]
        logger.info(f"Carregando modelo: {model_name} de {model_path}")

        try:
            # Detectar tipo de modelo
            is_xl = "xl" in model_name.lower()

            # Configurar torch dtype
            torch_dtype = torch.float16 if variant == "fp16" else torch.float32

            # Carregar pipeline apropriado
            if use_img2img:
                if is_xl:
                    pipeline = StableDiffusionXLPipeline.from_pretrained(
                        model_path,
                        torch_dtype=torch_dtype,
                        use_safetensors=True,
                        variant=variant
                    )
                else:
                    pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
                        model_path,
                        torch_dtype=torch_dtype,
                        use_safetensors=True,
                        variant=variant
                    )
            else:
                if is_xl:
                    pipeline = StableDiffusionXLPipeline.from_pretrained(
                        model_path,
                        torch_dtype=torch_dtype,
                        use_safetensors=True,
                        variant=variant
                    )
                else:
                    pipeline = StableDiffusionPipeline.from_pretrained(
                        model_path,
                        torch_dtype=torch_dtype,
                        use_safetensors=True,
                        variant=variant
                    )

            # Otimizações
            pipeline = pipeline.to(self.device)

            # Habilitar otimizações de memória
            if self.device == "cuda":
                pipeline.enable_attention_slicing()
                pipeline.enable_vae_slicing()

                # xformers se disponível
                try:
                    pipeline.enable_xformers_memory_efficient_attention()
                    logger.info("xformers habilitado")
                except:
                    logger.info("xformers não disponível")

            # Cache
            self.loaded_models[cache_key] = pipeline

            logger.info(f"Modelo carregado com sucesso: {model_name}")
            return pipeline

        except Exception as e:
            logger.error(f"Erro ao carregar modelo {model_name}: {e}")
            raise

    def _load_from_hub(self, model_id: str, use_img2img: bool = True) -> Any:
        """Carrega modelo do Hugging Face Hub como fallback"""
        logger.info(f"Tentando carregar do Hub: {model_id}")

        try:
            if use_img2img:
                pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
                    model_id,
                    torch_dtype=torch.float16,
                    use_safetensors=True
                )
            else:
                pipeline = StableDiffusionPipeline.from_pretrained(
                    model_id,
                    torch_dtype=torch.float16,
                    use_safetensors=True
                )

            pipeline = pipeline.to(self.device)

            if self.device == "cuda":
                pipeline.enable_attention_slicing()
                pipeline.enable_vae_slicing()

            return pipeline

        except Exception as e:
            logger.error(f"Erro ao carregar do Hub: {e}")
            raise

    def load_controlnet(
        self,
        controlnet_type: str = "canny"
    ) -> Any:
        """
        Carrega modelo ControlNet

        Args:
            controlnet_type: Tipo (canny, depth, pose, etc)

        Returns:
            Pipeline ControlNet
        """
        cache_key = f"controlnet_{controlnet_type}"

        if cache_key in self.loaded_models:
            return self.loaded_models[cache_key]

        logger.info(f"Carregando ControlNet: {controlnet_type}")

        # Mapeamento de modelos ControlNet
        controlnet_models = {
            "canny": "lllyasviel/control_v11p_sd15_canny",
            "depth": "lllyasviel/control_v11f1p_sd15_depth",
            "pose": "lllyasviel/control_v11p_sd15_openpose",
            "tile": "lllyasviel/control_v11f1e_sd15_tile"
        }

        model_id = controlnet_models.get(controlnet_type)
        if not model_id:
            raise ValueError(f"Tipo de ControlNet desconhecido: {controlnet_type}")

        try:
            # Carregar ControlNet
            controlnet = ControlNetModel.from_pretrained(
                model_id,
                torch_dtype=torch.float16
            )

            # Carregar pipeline SD com ControlNet
            pipeline = StableDiffusionControlNetPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                controlnet=controlnet,
                torch_dtype=torch.float16,
                use_safetensors=True
            )

            pipeline = pipeline.to(self.device)

            if self.device == "cuda":
                pipeline.enable_attention_slicing()
                pipeline.enable_vae_slicing()

            self.loaded_models[cache_key] = pipeline

            logger.info(f"ControlNet {controlnet_type} carregado")
            return pipeline

        except Exception as e:
            logger.error(f"Erro ao carregar ControlNet: {e}")
            raise

    def load_animatediff(
        self,
        model_name: Optional[str] = None
    ) -> Any:
        """
        Carrega modelo AnimateDiff

        Args:
            model_name: Nome do modelo base

        Returns:
            Pipeline AnimateDiff
        """
        cache_key = f"animatediff_{model_name}"

        if cache_key in self.loaded_models:
            return self.loaded_models[cache_key]

        logger.info("Carregando AnimateDiff...")

        try:
            # Usar modelo base Realistic Vision ou similar
            base_model = model_name or "SG161222/Realistic_Vision_V5.1_noVAE"

            # Carregar AnimateDiff
            pipeline = AnimateDiffPipeline.from_pretrained(
                base_model,
                torch_dtype=torch.float16
            )

            # Carregar módulo de movimento AnimateDiff
            pipeline.load_motion_adapter("guoyww/animatediff-motion-adapter-v1-5-2")

            # Scheduler otimizado
            pipeline.scheduler = DDIMScheduler.from_pretrained(
                base_model,
                subfolder="scheduler",
                clip_sample=False,
                timestep_spacing="linspace",
                beta_schedule="linear",
                steps_offset=1
            )

            pipeline = pipeline.to(self.device)

            if self.device == "cuda":
                pipeline.enable_attention_slicing()
                pipeline.enable_vae_slicing()

            self.loaded_models[cache_key] = pipeline

            logger.info("AnimateDiff carregado")
            return pipeline

        except Exception as e:
            logger.error(f"Erro ao carregar AnimateDiff: {e}")
            logger.info("AnimateDiff requer instalação adicional: pip install animatediff")
            raise

    def unload_model(self, cache_key: str):
        """Descarrega modelo da memória"""
        if cache_key in self.loaded_models:
            del self.loaded_models[cache_key]
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info(f"Modelo descarregado: {cache_key}")

    def unload_all(self):
        """Descarrega todos os modelos"""
        self.loaded_models.clear()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Todos os modelos descarregados")

    def get_memory_usage(self) -> Dict[str, float]:
        """Retorna uso de memória GPU"""
        if not torch.cuda.is_available():
            return {"message": "CUDA não disponível"}

        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3

        return {
            "allocated_gb": round(allocated, 2),
            "reserved_gb": round(reserved, 2),
            "total_gb": round(total, 2),
            "free_gb": round(total - allocated, 2)
        }

    def list_available_models(self) -> List[str]:
        """Lista modelos disponíveis"""
        return list(self.available_models.keys())
