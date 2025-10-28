"""
Pipeline híbrido que suporta modelos locais E API Gemini
Este é o novo pipeline principal recomendado
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from dotenv import load_dotenv
from PIL import Image
import logging
from tqdm import tqdm

# Importar componentes
sys.path.insert(0, str(Path(__file__).parent))

from model_manager import ModelManager
from local_frame_generator import LocalFrameGenerator
from frame_interpolation import FrameInterpolator
from gemini_api import GeminiAnimationGenerator
from cuda_processor import CUDAImageProcessor
from effects_generator import CosmicEffectsGenerator
from video_renderer import VideoRenderer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HybridFizaAnimator:
    """Pipeline híbrido de animação com suporte a modelos locais e API"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Inicializa pipeline híbrido

        Args:
            config_path: Caminho para configuração
        """
        load_dotenv()

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        logger.info(f"Configuração carregada: {self.config['project']['name']}")

        self._initialize_components()

    def _initialize_components(self):
        """Inicializa componentes do pipeline"""
        logger.info("Inicializando componentes...")

        # Verificar se usar modelos locais
        self.use_local_models = self.config.get('local_models', {}).get('enabled', False)

        # CUDA Processor (sempre necessário)
        cuda_config = self.config.get('cuda', {})
        self.cuda_processor = CUDAImageProcessor(
            device_id=cuda_config.get('device_id', 0),
            use_cuda=cuda_config.get('enabled', True)
        )

        # Efeitos
        self.effects = CosmicEffectsGenerator(self.config)

        # Renderizador
        self.renderer = VideoRenderer(self.config)

        if self.use_local_models:
            logger.info("Modo: MODELOS LOCAIS")
            self._init_local_models()
        else:
            logger.info("Modo: API GEMINI")
            self._init_gemini()

    def _init_local_models(self):
        """Inicializa modelos locais"""
        models_dir = self.config.get('local_models', {}).get('models_dir', 'models')

        # Model Manager
        self.model_manager = ModelManager(
            models_dir=models_dir,
            device="cuda" if self.cuda_processor.use_cuda else "cpu"
        )

        # Frame Generator
        self.local_generator = LocalFrameGenerator(
            self.config,
            self.model_manager
        )

        # Interpolador
        interp_config = self.config.get('local_models', {}).get('interpolation', {})
        self.interpolator = FrameInterpolator(
            device=self.model_manager.device,
            model_type=interp_config.get('method', 'rife')
        )

        logger.info("Modelos locais inicializados")
        logger.info(f"Modelos disponíveis: {self.model_manager.list_available_models()}")

    def _init_gemini(self):
        """Inicializa API Gemini"""
        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY não encontrada")

        self.gemini = GeminiAnimationGenerator(gemini_key, self.config)
        logger.info("API Gemini inicializada")

    def load_base_image(self, image_path: str) -> Image.Image:
        """Carrega imagem base"""
        logger.info(f"Carregando: {image_path}")

        image = Image.open(image_path)

        if image.mode != 'RGB':
            image = image.convert('RGB')

        logger.info(f"Imagem: {image.size}")
        return image

    def generate_keyframes(
        self,
        base_image: Image.Image,
        num_keyframes: Optional[int] = None
    ) -> List[Image.Image]:
        """
        Gera keyframes usando método configurado

        Args:
            base_image: Imagem base
            num_keyframes: Número de keyframes

        Returns:
            Lista de keyframes
        """
        if num_keyframes is None:
            fps = self.config.get('animation', {}).get('fps', 30)
            duration = self.config.get('animation', {}).get('duration', 5)

            if self.use_local_models:
                frames_between = 10  # Modelos locais são mais rápidos
            else:
                frames_between = self.config.get('gemini', {}).get(
                    'stop_motion', {}
                ).get('frames_between_generations', 5)

            total_frames = fps * duration
            num_keyframes = max(2, total_frames // frames_between)

        logger.info(f"Gerando {num_keyframes} keyframes...")

        if self.use_local_models:
            return self._generate_keyframes_local(base_image, num_keyframes)
        else:
            return self._generate_keyframes_gemini(base_image, num_keyframes)

    def _generate_keyframes_local(
        self,
        base_image: Image.Image,
        num_keyframes: int
    ) -> List[Image.Image]:
        """Gera keyframes com modelos locais"""
        gen_config = self.config.get('local_models', {}).get('generator', {})
        method = gen_config.get('method', 'img2img')

        # Obter prompt base
        prompts_config = self.config.get('local_models', {}).get('prompts', {})
        base_prompt = prompts_config.get('base', 'cosmic scene, space character')

        logger.info(f"Gerando keyframes locais (método: {method})")

        # Verificar se usar AnimateDiff
        animatediff_config = self.config.get('local_models', {}).get('animatediff', {})
        if animatediff_config.get('enabled', False):
            try:
                logger.info("Tentando usar AnimateDiff...")
                return self.local_generator.generate_with_animatediff(
                    base_image,
                    base_prompt,
                    num_frames=num_keyframes * 8  # AnimateDiff gera múltiplos de 8
                )
            except Exception as e:
                logger.warning(f"AnimateDiff falhou: {e}")
                logger.info("Fallback para img2img/controlnet")

        # Usar img2img ou controlnet
        keyframes = self.local_generator.generate_keyframes_sd(
            base_image=base_image,
            num_keyframes=num_keyframes,
            method=method,
            base_prompt=base_prompt
        )

        return keyframes

    def _generate_keyframes_gemini(
        self,
        base_image: Image.Image,
        num_keyframes: int
    ) -> List[Image.Image]:
        """Gera keyframes com Gemini"""
        keyframes = self.gemini.generate_keyframes(base_image, num_keyframes)

        if not keyframes or len(keyframes) < 2:
            logger.warning("Gemini retornou poucos keyframes, usando imagem base")
            keyframes = [base_image.copy() for _ in range(num_keyframes)]

        return keyframes

    def interpolate_all_frames(
        self,
        keyframes: List[Image.Image]
    ) -> List[Image.Image]:
        """
        Interpola frames completos

        Args:
            keyframes: Keyframes gerados

        Returns:
            Sequência completa
        """
        logger.info("Interpolando frames...")

        fps = self.config.get('animation', {}).get('fps', 30)
        duration = self.config.get('animation', {}).get('duration', 5)
        total_frames = fps * duration

        if self.use_local_models:
            # Usar interpolador avançado (RIFE/FILM)
            all_frames = self.interpolator.interpolate_sequence(
                keyframes,
                total_frames
            )
        else:
            # Usar CUDA processor com optical flow
            all_frames = self._interpolate_optical_flow(keyframes, total_frames)

        logger.info(f"Total de frames: {len(all_frames)}")
        return all_frames

    def _interpolate_optical_flow(
        self,
        keyframes: List[Image.Image],
        total_frames: int
    ) -> List[Image.Image]:
        """Interpolação usando optical flow (fallback)"""
        frames_per_segment = total_frames // (len(keyframes) - 1)
        all_frames = []

        for i in tqdm(range(len(keyframes) - 1), desc="Interpolando"):
            kf1 = keyframes[i]
            kf2 = keyframes[i + 1]

            if i == 0:
                all_frames.append(kf1)

            interpolated = self.cuda_processor.interpolate_frames(
                kf1, kf2,
                num_frames=frames_per_segment,
                method='optical_flow'
            )

            all_frames.extend(interpolated)

        all_frames.append(keyframes[-1])

        # Ajustar para total exato
        if len(all_frames) > total_frames:
            all_frames = all_frames[:total_frames]
        elif len(all_frames) < total_frames:
            while len(all_frames) < total_frames:
                all_frames.append(all_frames[-1].copy())

        return all_frames

    def apply_effects_to_frames(
        self,
        frames: List[Image.Image]
    ) -> List[Image.Image]:
        """Aplica efeitos cósmicos"""
        logger.info("Aplicando efeitos cósmicos...")

        processed = []

        for i, frame in enumerate(tqdm(frames, desc="Aplicando efeitos")):
            processed_frame = self.effects.apply_all_effects(frame, i)

            # Motion blur se habilitado
            motion_config = self.config.get('animation', {}).get('effects', {}).get('motion_blur', {})
            if motion_config.get('enabled', False):
                strength = motion_config.get('strength', 0.3)
                processed_frame = self.cuda_processor.add_motion_blur(
                    processed_frame,
                    angle=0,
                    strength=strength
                )

            processed.append(processed_frame)

        return processed

    def animate(
        self,
        image_path: str,
        output_dir: str = "assets/output",
        base_name: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Pipeline completo de animação

        Args:
            image_path: Imagem de entrada
            output_dir: Diretório de saída
            base_name: Nome base

        Returns:
            Vídeos gerados
        """
        logger.info("="*60)
        logger.info("FIZA HYBRID ANIMATOR")
        logger.info(f"Modo: {'MODELOS LOCAIS' if self.use_local_models else 'API GEMINI'}")
        logger.info("="*60)

        if base_name is None:
            base_name = Path(image_path).stem

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. Carregar imagem
        logger.info("\n[1/5] Carregando imagem...")
        base_image = self.load_base_image(image_path)

        # 2. Gerar keyframes
        logger.info("\n[2/5] Gerando keyframes...")
        keyframes = self.generate_keyframes(base_image)

        # Salvar keyframes
        keyframes_dir = output_path / "keyframes"
        keyframes_dir.mkdir(exist_ok=True)
        for i, kf in enumerate(keyframes):
            kf.save(keyframes_dir / f"keyframe_{i:03d}.png")
        logger.info(f"Keyframes salvos: {keyframes_dir}")

        # 3. Interpolar
        logger.info("\n[3/5] Interpolando frames...")
        all_frames = self.interpolate_all_frames(keyframes)

        # 4. Aplicar efeitos
        logger.info("\n[4/5] Aplicando efeitos...")
        frames_with_effects = self.apply_effects_to_frames(all_frames)

        # Samples
        samples_dir = output_path / "samples"
        samples_dir.mkdir(exist_ok=True)
        sample_indices = [0, len(frames_with_effects)//4, len(frames_with_effects)//2,
                         3*len(frames_with_effects)//4, len(frames_with_effects)-1]
        for idx in sample_indices:
            if idx < len(frames_with_effects):
                frames_with_effects[idx].save(samples_dir / f"frame_{idx:04d}.png")
        logger.info(f"Samples salvos: {samples_dir}")

        # 5. Renderizar
        logger.info("\n[5/5] Renderizando vídeos...")
        results = self.renderer.render_multiple_formats(
            base_image=base_image,
            frames_with_effects=frames_with_effects,
            output_dir=output_path,
            base_name=base_name
        )

        # GIF preview
        logger.info("\nCriando preview GIF...")
        gif_path = output_path / f"{base_name}_preview.gif"
        self.renderer.create_preview_gif(
            frames_with_effects[::3],
            gif_path
        )

        logger.info("\n" + "="*60)
        logger.info("CONCLUÍDO!")
        logger.info("="*60)
        logger.info("\nVídeos gerados:")
        for fmt, path in results.items():
            logger.info(f"  {fmt}: {path}")
        logger.info(f"\nPreview: {gif_path}")

        # Limpar memória se usando modelos locais
        if self.use_local_models:
            logger.info("\nLimpando memória GPU...")
            self.model_manager.unload_all()
            logger.info(f"Memória: {self.model_manager.get_memory_usage()}")

        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Fiza Hybrid Animator - Modelos Locais + API"
    )
    parser.add_argument('image', type=str, help='Imagem base')
    parser.add_argument('--output', type=str, default='assets/output', help='Diretório de saída')
    parser.add_argument('--config', type=str, default='config/config.yaml', help='Arquivo de configuração')
    parser.add_argument('--name', type=str, help='Nome base')
    parser.add_argument('--use-local', action='store_true', help='Forçar uso de modelos locais')
    parser.add_argument('--use-api', action='store_true', help='Forçar uso de API Gemini')

    args = parser.parse_args()

    if not Path(args.image).exists():
        logger.error(f"Imagem não encontrada: {args.image}")
        sys.exit(1)

    try:
        animator = HybridFizaAnimator(args.config)

        # Override config se flags especificadas
        if args.use_local:
            animator.use_local_models = True
            animator._init_local_models()
        elif args.use_api:
            animator.use_local_models = False
            animator._init_gemini()

        results = animator.animate(
            image_path=args.image,
            output_dir=args.output,
            base_name=args.name
        )

    except Exception as e:
        logger.error(f"Erro: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
