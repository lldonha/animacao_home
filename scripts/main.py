"""
Pipeline principal de animação Fiza - Exploradora Cósmica
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

# Adicionar diretório scripts ao path
sys.path.insert(0, str(Path(__file__).parent))

from gemini_api import GeminiAnimationGenerator
from cuda_processor import CUDAImageProcessor
from effects_generator import CosmicEffectsGenerator
from video_renderer import VideoRenderer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FizaAnimator:
    """Pipeline completo de animação da Fiza"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Inicializa pipeline de animação

        Args:
            config_path: Caminho para arquivo de configuração
        """
        # Carregar variáveis de ambiente
        load_dotenv()

        # Carregar configuração
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        logger.info(f"Configuração carregada: {self.config['project']['name']}")

        # Inicializar componentes
        self._initialize_components()

    def _initialize_components(self):
        """Inicializa todos os componentes do pipeline"""
        logger.info("Inicializando componentes...")

        # API Gemini
        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY não encontrada no .env")

        self.gemini = GeminiAnimationGenerator(gemini_key, self.config)

        # Processador CUDA
        cuda_config = self.config.get('cuda', {})
        self.cuda_processor = CUDAImageProcessor(
            device_id=cuda_config.get('device_id', 0),
            use_cuda=cuda_config.get('enabled', True)
        )

        # Gerador de efeitos
        self.effects = CosmicEffectsGenerator(self.config)

        # Renderizador de vídeo
        self.renderer = VideoRenderer(self.config)

        logger.info("Componentes inicializados com sucesso")

    def load_base_image(self, image_path: str) -> Image.Image:
        """
        Carrega e prepara imagem base

        Args:
            image_path: Caminho da imagem

        Returns:
            Imagem carregada
        """
        logger.info(f"Carregando imagem base: {image_path}")

        image = Image.open(image_path)

        # Converter para RGB se necessário
        if image.mode != 'RGB':
            image = image.convert('RGB')

        logger.info(f"Imagem carregada: {image.size}")

        return image

    def generate_keyframes(
        self,
        base_image: Image.Image,
        num_keyframes: Optional[int] = None
    ) -> List[Image.Image]:
        """
        Gera keyframes principais usando Gemini

        Args:
            base_image: Imagem base
            num_keyframes: Número de keyframes (None = calcular automaticamente)

        Returns:
            Lista de keyframes
        """
        if num_keyframes is None:
            # Calcular baseado na configuração
            fps = self.config.get('animation', {}).get('fps', 30)
            duration = self.config.get('animation', {}).get('duration', 5)
            frames_between = self.config.get('gemini', {}).get(
                'stop_motion', {}
            ).get('frames_between_generations', 5)

            total_frames = fps * duration
            num_keyframes = max(2, total_frames // frames_between)

        logger.info(f"Gerando {num_keyframes} keyframes com Gemini...")

        # Gerar keyframes usando Gemini
        keyframes = self.gemini.generate_keyframes(base_image, num_keyframes)

        # Se Gemini falhar, usar imagem base para todos
        if not keyframes or len(keyframes) < 2:
            logger.warning("Usando imagem base como keyframes")
            keyframes = [base_image.copy() for _ in range(num_keyframes)]

        return keyframes

    def interpolate_all_frames(
        self,
        keyframes: List[Image.Image]
    ) -> List[Image.Image]:
        """
        Interpola todos os frames entre keyframes

        Args:
            keyframes: Lista de keyframes

        Returns:
            Lista completa de frames
        """
        logger.info("Interpolando frames...")

        # Calcular frames por segmento
        fps = self.config.get('animation', {}).get('fps', 30)
        duration = self.config.get('animation', {}).get('duration', 5)
        total_frames = fps * duration

        frames_per_segment = total_frames // (len(keyframes) - 1)

        # Método de interpolação
        interp_method = self.config.get('gemini', {}).get(
            'stop_motion', {}
        ).get('interpolation_method', 'optical_flow')

        all_frames = []

        # Interpolar entre cada par de keyframes
        for i in tqdm(range(len(keyframes) - 1), desc="Interpolando segmentos"):
            kf1 = keyframes[i]
            kf2 = keyframes[i + 1]

            # Interpolar
            interpolated = self.cuda_processor.interpolate_frames(
                kf1, kf2,
                num_frames=frames_per_segment,
                method=interp_method
            )

            # Adicionar frames (exceto primeiro se não for início)
            if i == 0:
                all_frames.append(kf1)

            all_frames.extend(interpolated)

        # Adicionar último keyframe
        all_frames.append(keyframes[-1])

        # Ajustar para número exato de frames
        if len(all_frames) > total_frames:
            all_frames = all_frames[:total_frames]
        elif len(all_frames) < total_frames:
            # Duplicar último frame
            while len(all_frames) < total_frames:
                all_frames.append(all_frames[-1].copy())

        logger.info(f"Total de frames interpolados: {len(all_frames)}")
        return all_frames

    def apply_effects_to_frames(
        self,
        frames: List[Image.Image]
    ) -> List[Image.Image]:
        """
        Aplica efeitos cósmicos a todos os frames

        Args:
            frames: Lista de frames

        Returns:
            Frames com efeitos aplicados
        """
        logger.info("Aplicando efeitos cósmicos...")

        processed_frames = []

        for i, frame in enumerate(tqdm(frames, desc="Aplicando efeitos")):
            # Aplicar todos os efeitos
            processed = self.effects.apply_all_effects(frame, i)

            # Aplicar motion blur se habilitado
            motion_config = self.config.get('animation', {}).get('effects', {}).get('motion_blur', {})
            if motion_config.get('enabled', False):
                strength = motion_config.get('strength', 0.3)
                processed = self.cuda_processor.add_motion_blur(
                    processed,
                    angle=0,
                    strength=strength
                )

            processed_frames.append(processed)

        return processed_frames

    def animate(
        self,
        image_path: str,
        output_dir: str = "assets/output",
        base_name: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Executa pipeline completo de animação

        Args:
            image_path: Caminho da imagem base
            output_dir: Diretório de saída
            base_name: Nome base dos arquivos de saída

        Returns:
            Dicionário com formatos e caminhos dos vídeos gerados
        """
        logger.info("="*60)
        logger.info("INICIANDO PIPELINE DE ANIMAÇÃO FIZA")
        logger.info("="*60)

        # Nome base
        if base_name is None:
            base_name = Path(image_path).stem

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. Carregar imagem base
        logger.info("\n[1/5] Carregando imagem base...")
        base_image = self.load_base_image(image_path)

        # 2. Gerar keyframes com Gemini
        logger.info("\n[2/5] Gerando keyframes com Gemini...")
        keyframes = self.generate_keyframes(base_image)

        # Salvar keyframes para debug
        keyframes_dir = output_path / "keyframes"
        keyframes_dir.mkdir(exist_ok=True)
        for i, kf in enumerate(keyframes):
            kf.save(keyframes_dir / f"keyframe_{i:03d}.png")
        logger.info(f"Keyframes salvos em: {keyframes_dir}")

        # 3. Interpolar todos os frames
        logger.info("\n[3/5] Interpolando frames...")
        all_frames = self.interpolate_all_frames(keyframes)

        # 4. Aplicar efeitos cósmicos
        logger.info("\n[4/5] Aplicando efeitos cósmicos...")
        frames_with_effects = self.apply_effects_to_frames(all_frames)

        # Salvar alguns frames para debug
        samples_dir = output_path / "samples"
        samples_dir.mkdir(exist_ok=True)
        sample_indices = [0, len(frames_with_effects)//4, len(frames_with_effects)//2,
                         3*len(frames_with_effects)//4, len(frames_with_effects)-1]
        for idx in sample_indices:
            if idx < len(frames_with_effects):
                frames_with_effects[idx].save(samples_dir / f"frame_{idx:04d}.png")
        logger.info(f"Frames de amostra salvos em: {samples_dir}")

        # 5. Renderizar vídeos
        logger.info("\n[5/5] Renderizando vídeos...")
        results = self.renderer.render_multiple_formats(
            base_image=base_image,
            frames_with_effects=frames_with_effects,
            output_dir=output_path,
            base_name=base_name
        )

        # Criar preview GIF
        logger.info("\nCriando preview GIF...")
        gif_path = output_path / f"{base_name}_preview.gif"
        self.renderer.create_preview_gif(
            frames_with_effects[::3],  # Skip frames
            gif_path
        )

        logger.info("\n" + "="*60)
        logger.info("ANIMAÇÃO CONCLUÍDA COM SUCESSO!")
        logger.info("="*60)
        logger.info("\nVídeos gerados:")
        for format_name, path in results.items():
            logger.info(f"  {format_name}: {path}")
        logger.info(f"\nPreview GIF: {gif_path}")

        return results


def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fiza - Exploradora Cósmica Animator"
    )
    parser.add_argument(
        'image',
        type=str,
        help='Caminho da imagem base'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='assets/output',
        help='Diretório de saída'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Arquivo de configuração'
    )
    parser.add_argument(
        '--name',
        type=str,
        help='Nome base dos arquivos de saída'
    )

    args = parser.parse_args()

    # Verificar se imagem existe
    if not Path(args.image).exists():
        logger.error(f"Imagem não encontrada: {args.image}")
        sys.exit(1)

    # Criar animador
    try:
        animator = FizaAnimator(args.config)

        # Executar animação
        results = animator.animate(
            image_path=args.image,
            output_dir=args.output,
            base_name=args.name
        )

    except Exception as e:
        logger.error(f"Erro durante animação: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
