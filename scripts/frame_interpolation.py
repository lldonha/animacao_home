"""
Interpolação avançada de frames usando FILM, RIFE e outros modelos
"""

import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from typing import List, Optional
import logging
import cv2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FrameInterpolator:
    """Interpolação avançada de frames"""

    def __init__(self, device: str = "cuda", model_type: str = "rife"):
        """
        Inicializa interpolador

        Args:
            device: Dispositivo (cuda ou cpu)
            model_type: Tipo de modelo (rife, film, or optical_flow)
        """
        self.device = device if torch.cuda.is_available() else "cpu"
        self.model_type = model_type
        self.model = None

        # Carregar modelo
        self._load_model()

    def _load_model(self):
        """Carrega modelo de interpolação"""
        logger.info(f"Carregando modelo de interpolação: {self.model_type}")

        if self.model_type == "rife":
            self._load_rife()
        elif self.model_type == "film":
            self._load_film()
        else:
            logger.info("Usando optical flow (não requer modelo)")

    def _load_rife(self):
        """Carrega RIFE (Real-Time Intermediate Flow Estimation)"""
        try:
            # Tentar importar RIFE
            from rife_arch import IFNet

            logger.info("Carregando RIFE...")

            # Modelo RIFE v4.6 (mais recente)
            model_path = "models/interpolation/rife_v4.6.pkl"

            self.model = IFNet().to(self.device)

            # Carregar pesos se existirem
            try:
                checkpoint = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(checkpoint)
                self.model.eval()
                logger.info("RIFE carregado com sucesso")
            except FileNotFoundError:
                logger.warning(f"Modelo RIFE não encontrado em {model_path}")
                logger.info("Usando optical flow como fallback")
                self.model_type = "optical_flow"

        except ImportError:
            logger.warning("RIFE não instalado. Install: pip install rife-ncnn-vulkan-python")
            logger.info("Usando optical flow como fallback")
            self.model_type = "optical_flow"

    def _load_film(self):
        """Carrega FILM (Frame Interpolation for Large Motion)"""
        try:
            logger.info("Carregando FILM...")

            # FILM via TensorFlow Hub
            import tensorflow_hub as hub

            model_path = "https://tfhub.dev/google/film/1"
            self.model = hub.load(model_path)

            logger.info("FILM carregado com sucesso")

        except ImportError:
            logger.warning("TensorFlow não disponível para FILM")
            logger.info("Usando RIFE ou optical flow como fallback")
            self.model_type = "rife"
            self._load_rife()
        except Exception as e:
            logger.error(f"Erro ao carregar FILM: {e}")
            self.model_type = "optical_flow"

    def interpolate_frames(
        self,
        frame1: Image.Image,
        frame2: Image.Image,
        num_frames: int = 5
    ) -> List[Image.Image]:
        """
        Interpola frames entre duas imagens

        Args:
            frame1: Frame inicial
            frame2: Frame final
            num_frames: Número de frames intermediários

        Returns:
            Lista de frames interpolados (sem incluir frame1 e frame2)
        """
        if self.model_type == "rife" and self.model is not None:
            return self._interpolate_rife(frame1, frame2, num_frames)
        elif self.model_type == "film" and self.model is not None:
            return self._interpolate_film(frame1, frame2, num_frames)
        else:
            return self._interpolate_optical_flow(frame1, frame2, num_frames)

    def _interpolate_rife(
        self,
        frame1: Image.Image,
        frame2: Image.Image,
        num_frames: int
    ) -> List[Image.Image]:
        """Interpolação usando RIFE"""
        logger.info(f"Interpolando {num_frames} frames com RIFE...")

        # Converter para tensors
        img1 = self._pil_to_tensor(frame1)
        img2 = self._pil_to_tensor(frame2)

        interpolated = []

        with torch.no_grad():
            for i in range(1, num_frames + 1):
                t = i / (num_frames + 1)

                # RIFE aceita timestep entre 0 e 1
                timestep = torch.tensor([t], device=self.device)

                # Interpolar
                result = self.model(img1, img2, timestep)

                # Converter de volta para PIL
                pil_img = self._tensor_to_pil(result)
                interpolated.append(pil_img)

        return interpolated

    def _interpolate_film(
        self,
        frame1: Image.Image,
        frame2: Image.Image,
        num_frames: int
    ) -> List[Image.Image]:
        """Interpolação usando FILM"""
        logger.info(f"Interpolando {num_frames} frames com FILM...")

        import tensorflow as tf

        # Converter para numpy arrays
        img1_np = np.array(frame1) / 255.0
        img2_np = np.array(frame2) / 255.0

        # Converter para tensors TF
        img1_tf = tf.convert_to_tensor(img1_np[None, ...], dtype=tf.float32)
        img2_tf = tf.convert_to_tensor(img2_np[None, ...], dtype=tf.float32)

        interpolated = []

        for i in range(1, num_frames + 1):
            t = i / (num_frames + 1)

            # FILM interpola com timestep
            result = self.model({
                'x0': img1_tf,
                'x1': img2_tf,
                'time': tf.constant([t], dtype=tf.float32)
            })

            # Converter de volta
            result_np = (result['image'][0].numpy() * 255).astype(np.uint8)
            pil_img = Image.fromarray(result_np)
            interpolated.append(pil_img)

        return interpolated

    def _interpolate_optical_flow(
        self,
        frame1: Image.Image,
        frame2: Image.Image,
        num_frames: int
    ) -> List[Image.Image]:
        """Interpolação usando optical flow (fallback)"""
        logger.info(f"Interpolando {num_frames} frames com optical flow...")

        # Converter para OpenCV
        img1 = cv2.cvtColor(np.array(frame1), cv2.COLOR_RGB2BGR)
        img2 = cv2.cvtColor(np.array(frame2), cv2.COLOR_RGB2BGR)

        # Calcular optical flow
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        flow = cv2.calcOpticalFlowFarneback(
            gray1, gray2, None,
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0
        )

        interpolated = []
        h, w = img1.shape[:2]

        for i in range(1, num_frames + 1):
            t = i / (num_frames + 1)

            # Interpolar flow
            flow_t = flow * t

            # Criar grid de mapeamento
            map_x = np.arange(w, dtype=np.float32)
            map_y = np.arange(h, dtype=np.float32)
            map_x, map_y = np.meshgrid(map_x, map_y)

            map_x = map_x + flow_t[:, :, 0]
            map_y = map_y + flow_t[:, :, 1]

            # Warp image
            warped = cv2.remap(img1, map_x, map_y, cv2.INTER_LINEAR)

            # Blend com frame 2 para suavizar
            blended = cv2.addWeighted(warped, 1 - t, img2, t, 0)

            # Converter de volta para PIL
            result = cv2.cvtColor(blended, cv2.COLOR_BGR2RGB)
            interpolated.append(Image.fromarray(result))

        return interpolated

    def interpolate_sequence(
        self,
        frames: List[Image.Image],
        target_count: int
    ) -> List[Image.Image]:
        """
        Interpola sequência de frames para atingir contagem alvo

        Args:
            frames: Lista de keyframes
            target_count: Número total de frames desejado

        Returns:
            Sequência interpolada completa
        """
        logger.info(f"Interpolando sequência: {len(frames)} -> {target_count} frames")

        if len(frames) >= target_count:
            # Já temos frames suficientes, fazer downsample
            indices = np.linspace(0, len(frames) - 1, target_count, dtype=int)
            return [frames[i] for i in indices]

        # Calcular quantos frames interpolar entre cada par
        segments = len(frames) - 1
        frames_per_segment = (target_count - len(frames)) // segments
        remainder = (target_count - len(frames)) % segments

        result = []

        for i in range(segments):
            result.append(frames[i])

            # Interpolar
            num_interpolated = frames_per_segment
            if i < remainder:
                num_interpolated += 1

            if num_interpolated > 0:
                interpolated = self.interpolate_frames(
                    frames[i],
                    frames[i + 1],
                    num_interpolated
                )
                result.extend(interpolated)

        # Adicionar último frame
        result.append(frames[-1])

        logger.info(f"Sequência interpolada: {len(result)} frames")
        return result

    def _pil_to_tensor(self, image: Image.Image) -> torch.Tensor:
        """Converte PIL para tensor PyTorch"""
        img_array = np.array(image).astype(np.float32) / 255.0

        # HWC -> CHW
        if len(img_array.shape) == 3:
            img_tensor = torch.from_numpy(img_array).permute(2, 0, 1)
        else:
            img_tensor = torch.from_numpy(img_array).unsqueeze(0)

        return img_tensor.unsqueeze(0).to(self.device)

    def _tensor_to_pil(self, tensor: torch.Tensor) -> Image.Image:
        """Converte tensor para PIL"""
        tensor = tensor.squeeze(0).cpu()

        # CHW -> HWC
        if tensor.shape[0] in [1, 3, 4]:
            tensor = tensor.permute(1, 2, 0)

        img_array = (tensor.numpy() * 255).astype(np.uint8)
        return Image.fromarray(img_array)

    def batch_interpolate(
        self,
        frame_pairs: List[tuple],
        num_frames_each: int = 5
    ) -> List[List[Image.Image]]:
        """
        Interpola múltiplos pares de frames em batch

        Args:
            frame_pairs: Lista de tuplas (frame1, frame2)
            num_frames_each: Frames intermediários por par

        Returns:
            Lista de listas de frames interpolados
        """
        logger.info(f"Interpolação em batch: {len(frame_pairs)} pares")

        results = []

        for i, (f1, f2) in enumerate(frame_pairs):
            logger.info(f"Interpolando par {i+1}/{len(frame_pairs)}")
            interpolated = self.interpolate_frames(f1, f2, num_frames_each)
            results.append(interpolated)

        return results
