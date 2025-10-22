"""
Processador de imagens acelerado por CUDA para efeitos e interpolação
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import List, Tuple, Optional
from PIL import Image
import cv2
import logging

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    logging.warning("CuPy não disponível - usando processamento CPU")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CUDAImageProcessor:
    """Processador de imagens usando CUDA para máxima performance"""

    def __init__(self, device_id: int = 0, use_cuda: bool = True):
        """
        Inicializa processador CUDA

        Args:
            device_id: ID da GPU (0 para RTX 4070)
            use_cuda: Usar CUDA se disponível
        """
        self.use_cuda = use_cuda and torch.cuda.is_available()

        if self.use_cuda:
            self.device = torch.device(f'cuda:{device_id}')
            torch.cuda.set_device(device_id)

            # Informações da GPU
            gpu_name = torch.cuda.get_device_name(device_id)
            gpu_memory = torch.cuda.get_device_properties(device_id).total_memory / 1e9

            logger.info(f"CUDA ativado: {gpu_name} ({gpu_memory:.1f} GB)")
            logger.info(f"CUDA Version: {torch.version.cuda}")
        else:
            self.device = torch.device('cpu')
            logger.warning("CUDA não disponível - usando CPU")

        # Habilitar CuDNN para otimização
        if self.use_cuda:
            torch.backends.cudnn.enabled = True
            torch.backends.cudnn.benchmark = True

    def pil_to_tensor(self, image: Image.Image) -> torch.Tensor:
        """Converte PIL Image para tensor PyTorch"""
        img_array = np.array(image).astype(np.float32) / 255.0

        # HWC -> CHW
        if len(img_array.shape) == 3:
            img_tensor = torch.from_numpy(img_array).permute(2, 0, 1)
        else:
            img_tensor = torch.from_numpy(img_array).unsqueeze(0)

        return img_tensor.unsqueeze(0).to(self.device)  # Add batch dimension

    def tensor_to_pil(self, tensor: torch.Tensor) -> Image.Image:
        """Converte tensor PyTorch para PIL Image"""
        # Remove batch dimension e move para CPU
        tensor = tensor.squeeze(0).cpu()

        # CHW -> HWC
        if tensor.shape[0] in [1, 3, 4]:  # Channel-first
            tensor = tensor.permute(1, 2, 0)

        # Converter para numpy e escalar
        img_array = (tensor.numpy() * 255).astype(np.uint8)

        return Image.fromarray(img_array)

    def interpolate_frames(
        self,
        frame1: Image.Image,
        frame2: Image.Image,
        num_frames: int = 5,
        method: str = 'optical_flow'
    ) -> List[Image.Image]:
        """
        Interpola frames entre duas imagens

        Args:
            frame1: Frame inicial
            frame2: Frame final
            num_frames: Número de frames intermediários
            method: Método de interpolação (optical_flow, blend, morph)

        Returns:
            Lista de frames interpolados
        """
        if method == 'optical_flow':
            return self._interpolate_optical_flow(frame1, frame2, num_frames)
        elif method == 'blend':
            return self._interpolate_blend(frame1, frame2, num_frames)
        else:
            return self._interpolate_morph(frame1, frame2, num_frames)

    def _interpolate_blend(
        self,
        frame1: Image.Image,
        frame2: Image.Image,
        num_frames: int
    ) -> List[Image.Image]:
        """Interpolação simples por blending"""
        tensor1 = self.pil_to_tensor(frame1)
        tensor2 = self.pil_to_tensor(frame2)

        interpolated = []

        for i in range(num_frames):
            alpha = (i + 1) / (num_frames + 1)
            blended = (1 - alpha) * tensor1 + alpha * tensor2
            interpolated.append(self.tensor_to_pil(blended))

        return interpolated

    def _interpolate_optical_flow(
        self,
        frame1: Image.Image,
        frame2: Image.Image,
        num_frames: int
    ) -> List[Image.Image]:
        """Interpolação usando optical flow (mais suave)"""
        # Converter para OpenCV
        img1 = cv2.cvtColor(np.array(frame1), cv2.COLOR_RGB2BGR)
        img2 = cv2.cvtColor(np.array(frame2), cv2.COLOR_RGB2BGR)

        # Calcular optical flow
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        flow = cv2.calcOpticalFlowFarneback(
            gray1, gray2, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )

        interpolated = []
        h, w = img1.shape[:2]

        for i in range(num_frames):
            t = (i + 1) / (num_frames + 1)

            # Interpolar flow
            flow_t = flow * t

            # Criar grid de mapeamento
            map_x = np.arange(w, dtype=np.float32)
            map_y = np.arange(h, dtype=np.float32)
            map_x, map_y = np.meshgrid(map_x, map_y)

            map_x = map_x + flow_t[:, :, 0]
            map_y = map_y + flow_t[:, :, 1]

            # Warped image
            warped = cv2.remap(img1, map_x, map_y, cv2.INTER_LINEAR)

            # Blend com frame 2 para suavizar
            blended = cv2.addWeighted(warped, 1-t, img2, t, 0)

            # Converter de volta para PIL
            result = cv2.cvtColor(blended, cv2.COLOR_BGR2RGB)
            interpolated.append(Image.fromarray(result))

        return interpolated

    def _interpolate_morph(
        self,
        frame1: Image.Image,
        frame2: Image.Image,
        num_frames: int
    ) -> List[Image.Image]:
        """Interpolação com morphing"""
        # Simplificado - usa blend com suavização
        return self._interpolate_blend(frame1, frame2, num_frames)

    def apply_glow_effect(
        self,
        image: Image.Image,
        intensity: float = 0.8,
        radius: int = 15,
        color: Tuple[int, int, int] = (100, 200, 255)
    ) -> Image.Image:
        """
        Aplica efeito de glow cósmico

        Args:
            image: Imagem de entrada
            intensity: Intensidade do glow (0-1)
            radius: Raio do blur
            color: Cor do glow em RGB

        Returns:
            Imagem com efeito glow
        """
        tensor = self.pil_to_tensor(image)

        # Criar máscara de brilho (áreas claras)
        brightness = tensor.mean(dim=1, keepdim=True)
        glow_mask = torch.clamp(brightness - 0.5, 0, 1) * 2

        # Aplicar blur gaussiano
        kernel_size = radius * 2 + 1
        glow_blurred = F.avg_pool2d(
            glow_mask,
            kernel_size=kernel_size,
            stride=1,
            padding=kernel_size // 2
        )

        # Criar camada de glow colorida
        glow_color = torch.tensor(color, device=self.device).view(1, 3, 1, 1) / 255.0
        glow_layer = glow_blurred * glow_color * intensity

        # Combinar com imagem original (screen blend)
        result = tensor + glow_layer * (1 - tensor)
        result = torch.clamp(result, 0, 1)

        return self.tensor_to_pil(result)

    def add_motion_blur(
        self,
        image: Image.Image,
        angle: float = 0,
        strength: float = 0.3
    ) -> Image.Image:
        """Adiciona motion blur para sensação de movimento"""
        img_array = np.array(image)

        # Criar kernel de motion blur
        size = int(20 * strength)
        if size % 2 == 0:
            size += 1

        kernel = np.zeros((size, size))
        kernel[int((size-1)/2), :] = np.ones(size)
        kernel = kernel / size

        # Rotacionar kernel
        M = cv2.getRotationMatrix2D((size/2, size/2), angle, 1.0)
        kernel = cv2.warpAffine(kernel, M, (size, size))

        # Aplicar blur
        result = cv2.filter2D(img_array, -1, kernel)

        return Image.fromarray(result)

    def upscale_image(
        self,
        image: Image.Image,
        scale: int = 2,
        method: str = 'bicubic'
    ) -> Image.Image:
        """
        Upscale de imagem usando GPU

        Args:
            image: Imagem de entrada
            scale: Fator de escala
            method: Método (bicubic, bilinear, nearest)

        Returns:
            Imagem upscaled
        """
        tensor = self.pil_to_tensor(image)

        # Upscale usando PyTorch
        upscaled = F.interpolate(
            tensor,
            scale_factor=scale,
            mode=method,
            align_corners=False if method != 'nearest' else None
        )

        return self.tensor_to_pil(upscaled)
