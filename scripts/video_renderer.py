"""
Renderizador de vídeo com suporte para múltiplos formatos e GPU acceleration
"""

import cv2
import numpy as np
from PIL import Image
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import logging
from moviepy.editor import ImageSequenceClip, concatenate_videoclips
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoRenderer:
    """Renderizador de vídeo com aceleração GPU"""

    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa renderizador

        Args:
            config: Configurações do projeto
        """
        self.config = config
        self.render_config = config.get('rendering', {})

        # Verificar suporte NVENC (GPU encoding)
        self.gpu_encoding = self._check_nvenc_support()

        if self.gpu_encoding:
            logger.info("NVENC disponível - usando GPU encoding")
        else:
            logger.info("NVENC não disponível - usando CPU encoding")

    def _check_nvenc_support(self) -> bool:
        """Verifica se NVENC está disponível"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True,
                text=True
            )
            return 'h264_nvenc' in result.stdout
        except Exception:
            return False

    def create_pan_sequence(
        self,
        base_image: Image.Image,
        direction: str,
        target_resolution: Tuple[int, int],
        num_frames: int
    ) -> List[Image.Image]:
        """
        Cria sequência de pan (esquerda->direita ou cima->baixo)

        Args:
            base_image: Imagem base (assumida 1:1)
            direction: 'horizontal' ou 'vertical'
            target_resolution: Resolução alvo (width, height)
            num_frames: Número de frames

        Returns:
            Lista de frames com pan aplicado
        """
        logger.info(f"Criando sequência pan {direction} com {num_frames} frames")

        frames = []
        target_w, target_h = target_resolution
        base_w, base_h = base_image.size

        # Garantir que imagem base é grande o suficiente
        if direction == 'horizontal':
            # Para 9:16, precisamos pan horizontal
            required_width = int(base_h * (target_w / target_h))
            if base_w < required_width:
                logger.warning(f"Imagem muito pequena para pan. Redimensionando...")
                base_image = base_image.resize((required_width, base_h), Image.LANCZOS)
                base_w = required_width

            crop_h = base_h
            crop_w = int(crop_h * (target_w / target_h))

            for i in range(num_frames):
                # Calcular posição do crop (esquerda para direita)
                progress = i / (num_frames - 1) if num_frames > 1 else 0
                x = int(progress * (base_w - crop_w))
                y = 0

                # Crop e resize
                cropped = base_image.crop((x, y, x + crop_w, y + crop_h))
                resized = cropped.resize(target_resolution, Image.LANCZOS)
                frames.append(resized)

        else:  # vertical
            # Para 16:9, precisamos pan vertical
            required_height = int(base_w * (target_h / target_w))
            if base_h < required_height:
                logger.warning(f"Imagem muito pequena para pan. Redimensionando...")
                base_image = base_image.resize((base_w, required_height), Image.LANCZOS)
                base_h = required_height

            crop_w = base_w
            crop_h = int(crop_w * (target_h / target_w))

            for i in range(num_frames):
                # Calcular posição do crop (cima para baixo)
                progress = i / (num_frames - 1) if num_frames > 1 else 0
                x = 0
                y = int(progress * (base_h - crop_h))

                # Crop e resize
                cropped = base_image.crop((x, y, x + crop_w, y + crop_h))
                resized = cropped.resize(target_resolution, Image.LANCZOS)
                frames.append(resized)

        logger.info(f"Sequência pan criada: {len(frames)} frames")
        return frames

    def render_video(
        self,
        frames: List[Image.Image],
        output_path: Path,
        fps: int = 30,
        audio_path: Optional[Path] = None
    ) -> bool:
        """
        Renderiza vídeo a partir de frames

        Args:
            frames: Lista de frames (PIL Images)
            output_path: Caminho de saída
            fps: Frames por segundo
            audio_path: Caminho do áudio (opcional)

        Returns:
            True se sucesso
        """
        try:
            logger.info(f"Renderizando vídeo: {output_path}")
            logger.info(f"Frames: {len(frames)}, FPS: {fps}")

            # Converter PIL Images para numpy arrays
            frame_arrays = [np.array(frame) for frame in frames]

            # Criar clip usando moviepy
            clip = ImageSequenceClip(frame_arrays, fps=fps)

            # Adicionar áudio se fornecido
            if audio_path and audio_path.exists():
                from moviepy.editor import AudioFileClip
                audio = AudioFileClip(str(audio_path))
                clip = clip.set_audio(audio)

            # Configurar codec e qualidade
            codec = self.render_config.get('codec', 'libx264')
            bitrate = self.render_config.get('bitrate', '8000k')

            # Usar GPU encoding se disponível
            if self.gpu_encoding:
                codec = 'h264_nvenc'
                logger.info(f"Usando GPU encoding: {codec}")

            # Escrever vídeo
            clip.write_videofile(
                str(output_path),
                fps=fps,
                codec=codec,
                bitrate=bitrate,
                audio_codec='aac' if audio_path else None,
                preset='slow' if codec == 'libx264' else 'p7',
                ffmpeg_params=['-pix_fmt', 'yuv420p']
            )

            clip.close()

            logger.info(f"Vídeo renderizado com sucesso: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao renderizar vídeo: {e}")
            return False

    def render_multiple_formats(
        self,
        base_image: Image.Image,
        frames_with_effects: List[Image.Image],
        output_dir: Path,
        base_name: str = "fiza_animation"
    ) -> Dict[str, Path]:
        """
        Renderiza vídeo em múltiplos formatos

        Args:
            base_image: Imagem base para pan
            frames_with_effects: Frames já processados (sem pan)
            output_dir: Diretório de saída
            base_name: Nome base dos arquivos

        Returns:
            Dicionário com formato -> caminho
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        results = {}

        # Obter configurações
        fps = self.config.get('animation', {}).get('fps', 30)
        duration = self.config.get('animation', {}).get('duration', 5)
        num_frames = fps * duration

        # Verificar se temos frames suficientes
        if len(frames_with_effects) < num_frames:
            logger.warning(f"Frames insuficientes: {len(frames_with_effects)}/{num_frames}")
            # Interpolar ou repetir frames conforme necessário
            frames_with_effects = self._adjust_frame_count(frames_with_effects, num_frames)

        # Formato 1: Short vertical (9:16) - Pan horizontal
        logger.info("Renderizando formato 9:16 (Short vertical)...")
        short_config = self.config.get('output_formats', {}).get('short_vertical', {})
        short_resolution = tuple(short_config.get('resolution', [1080, 1920]))

        # Criar sequência com pan horizontal
        short_frames = []
        for i, effect_frame in enumerate(frames_with_effects):
            # Aplicar pan na imagem base
            pan_frames = self.create_pan_sequence(
                base_image=effect_frame,
                direction='horizontal',
                target_resolution=short_resolution,
                num_frames=1  # Um frame por vez
            )
            if pan_frames:
                short_frames.append(pan_frames[0])

        short_output = output_dir / f"{base_name}_9x16.mp4"
        if self.render_video(short_frames, short_output, fps):
            results['9:16'] = short_output

        # Formato 2: Video horizontal (16:9) - Pan vertical
        logger.info("Renderizando formato 16:9 (Video horizontal)...")
        video_config = self.config.get('output_formats', {}).get('video_horizontal', {})
        video_resolution = tuple(video_config.get('resolution', [1920, 1080]))

        # Criar sequência com pan vertical
        video_frames = []
        for i, effect_frame in enumerate(frames_with_effects):
            # Aplicar pan na imagem base
            pan_frames = self.create_pan_sequence(
                base_image=effect_frame,
                direction='vertical',
                target_resolution=video_resolution,
                num_frames=1
            )
            if pan_frames:
                video_frames.append(pan_frames[0])

        video_output = output_dir / f"{base_name}_16x9.mp4"
        if self.render_video(video_frames, video_output, fps):
            results['16:9'] = video_output

        return results

    def _adjust_frame_count(
        self,
        frames: List[Image.Image],
        target_count: int
    ) -> List[Image.Image]:
        """Ajusta número de frames para o alvo (interpolação ou repetição)"""
        if len(frames) == target_count:
            return frames

        if len(frames) > target_count:
            # Reduzir frames uniformemente
            indices = np.linspace(0, len(frames) - 1, target_count, dtype=int)
            return [frames[i] for i in indices]
        else:
            # Interpolar frames
            # Simplificado: repetir frames uniformemente
            result = []
            ratio = target_count / len(frames)

            for i, frame in enumerate(frames):
                repeat_count = int(ratio)
                if (i + 1) * ratio - int((i + 1) * ratio) > i * ratio - int(i * ratio):
                    repeat_count += 1

                for _ in range(repeat_count):
                    result.append(frame.copy())

                if len(result) >= target_count:
                    break

            return result[:target_count]

    def create_preview_gif(
        self,
        frames: List[Image.Image],
        output_path: Path,
        fps: int = 15,
        optimize: bool = True
    ) -> bool:
        """
        Cria GIF preview da animação

        Args:
            frames: Lista de frames
            output_path: Caminho de saída
            fps: Frames por segundo
            optimize: Otimizar tamanho

        Returns:
            True se sucesso
        """
        try:
            duration = int(1000 / fps)  # milliseconds per frame

            # Redimensionar para preview
            preview_size = (480, 480)
            preview_frames = [
                frame.resize(preview_size, Image.LANCZOS)
                for frame in frames[::2]  # Skip frames para tamanho menor
            ]

            # Salvar GIF
            preview_frames[0].save(
                output_path,
                save_all=True,
                append_images=preview_frames[1:],
                duration=duration,
                loop=0,
                optimize=optimize
            )

            logger.info(f"Preview GIF criado: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar GIF: {e}")
            return False
