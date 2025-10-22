"""
Gerador de efeitos visuais cósmicos (partículas, glow, etc)
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from typing import List, Tuple, Dict, Any
import random
import math
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Particle:
    """Representa uma partícula cósmica individual"""

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        size: float,
        color: Tuple[int, int, int],
        lifetime: int
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.lifetime = lifetime
        self.age = 0
        self.alpha = 255

    def update(self):
        """Atualiza posição e estado da partícula"""
        self.x += self.vx
        self.y += self.vy
        self.age += 1

        # Fade out no final da vida
        life_ratio = self.age / self.lifetime
        self.alpha = int(255 * (1 - life_ratio))

    def is_alive(self) -> bool:
        """Verifica se partícula ainda está viva"""
        return self.age < self.lifetime


class CosmicEffectsGenerator:
    """Gerador de efeitos visuais cósmicos"""

    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa gerador de efeitos

        Args:
            config: Configurações do projeto
        """
        self.config = config
        self.effects_config = config.get('animation', {}).get('effects', {})
        self.particles: List[Particle] = []

    def initialize_particles(self, width: int, height: int):
        """Inicializa sistema de partículas"""
        particles_config = self.effects_config.get('particles', {})

        if not particles_config.get('enabled', True):
            return

        count = particles_config.get('count', 200)
        size_range = particles_config.get('size_range', [2, 8])
        speed_range = particles_config.get('speed_range', [0.5, 2.0])
        lifetime = particles_config.get('lifetime', 60)
        colors = particles_config.get('colors', [[255, 255, 200]])

        self.particles = []

        for _ in range(count):
            x = random.uniform(0, width)
            y = random.uniform(0, height)

            # Velocidade aleatória
            speed = random.uniform(*speed_range)
            angle = random.uniform(0, 2 * math.pi)
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)

            # Tamanho e cor aleatórios
            size = random.uniform(*size_range)
            color = tuple(random.choice(colors))

            particle = Particle(x, y, vx, vy, size, color, lifetime)
            self.particles.append(particle)

        logger.info(f"Inicializadas {len(self.particles)} partículas")

    def update_particles(self, width: int, height: int):
        """Atualiza todas as partículas"""
        particles_config = self.effects_config.get('particles', {})

        # Atualizar partículas existentes
        for particle in self.particles:
            particle.update()

            # Wrap around nas bordas
            if particle.x < 0:
                particle.x = width
            elif particle.x > width:
                particle.x = 0

            if particle.y < 0:
                particle.y = height
            elif particle.y > height:
                particle.y = 0

        # Remover partículas mortas e criar novas
        self.particles = [p for p in self.particles if p.is_alive()]

        # Repor partículas
        target_count = particles_config.get('count', 200)
        while len(self.particles) < target_count:
            self._spawn_particle(width, height)

    def _spawn_particle(self, width: int, height: int):
        """Cria uma nova partícula"""
        particles_config = self.effects_config.get('particles', {})

        x = random.uniform(0, width)
        y = random.uniform(0, height)

        speed_range = particles_config.get('speed_range', [0.5, 2.0])
        speed = random.uniform(*speed_range)
        angle = random.uniform(0, 2 * math.pi)
        vx = speed * math.cos(angle)
        vy = speed * math.sin(angle)

        size_range = particles_config.get('size_range', [2, 8])
        size = random.uniform(*size_range)

        colors = particles_config.get('colors', [[255, 255, 200]])
        color = tuple(random.choice(colors))

        lifetime = particles_config.get('lifetime', 60)

        particle = Particle(x, y, vx, vy, size, color, lifetime)
        self.particles.append(particle)

    def render_particles(self, image: Image.Image) -> Image.Image:
        """
        Renderiza partículas sobre a imagem

        Args:
            image: Imagem base

        Returns:
            Imagem com partículas
        """
        if not self.effects_config.get('particles', {}).get('enabled', True):
            return image

        # Criar camada de partículas
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        for particle in self.particles:
            # Desenhar partícula com glow
            x, y = int(particle.x), int(particle.y)
            size = particle.size

            # Glow externo
            for i in range(3):
                glow_size = size + i * 2
                glow_alpha = int(particle.alpha * 0.3 / (i + 1))
                glow_color = particle.color + (glow_alpha,)

                draw.ellipse(
                    [x - glow_size, y - glow_size, x + glow_size, y + glow_size],
                    fill=glow_color
                )

            # Partícula principal
            main_color = particle.color + (particle.alpha,)
            draw.ellipse(
                [x - size, y - size, x + size, y + size],
                fill=main_color
            )

        # Combinar com imagem
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        result = Image.alpha_composite(image, overlay)

        return result.convert('RGB')

    def apply_cosmic_glow(
        self,
        image: Image.Image,
        intensity: float = 0.8,
        radius: int = 15
    ) -> Image.Image:
        """
        Aplica efeito de glow cósmico

        Args:
            image: Imagem de entrada
            intensity: Intensidade do glow
            radius: Raio do glow

        Returns:
            Imagem com glow
        """
        glow_config = self.effects_config.get('glow', {})

        if not glow_config.get('enabled', True):
            return image

        intensity = glow_config.get('intensity', intensity)
        radius = glow_config.get('radius', radius)

        # Criar camada de glow
        glow_layer = image.copy()

        # Aumentar brilho das áreas claras
        enhancer = ImageEnhance.Brightness(glow_layer)
        glow_layer = enhancer.enhance(1.5)

        # Aplicar blur gaussiano
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=radius))

        # Blend com original usando screen mode
        result = Image.blend(image, glow_layer, intensity * 0.5)

        return result

    def add_lens_flare(
        self,
        image: Image.Image,
        position: Tuple[int, int],
        intensity: float = 0.7
    ) -> Image.Image:
        """
        Adiciona lens flare na posição especificada

        Args:
            image: Imagem de entrada
            position: Posição (x, y) do flare
            intensity: Intensidade do efeito

        Returns:
            Imagem com lens flare
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        x, y = position

        # Criar múltiplos círculos de flare
        flare_sizes = [100, 60, 30, 15, 8]
        for i, size in enumerate(flare_sizes):
            alpha = int(255 * intensity * 0.3 / (i + 1))
            color = (255, 255, 200, alpha)

            draw.ellipse(
                [x - size, y - size, x + size, y + size],
                fill=color
            )

        # Combinar
        result = Image.alpha_composite(image, overlay)
        return result.convert('RGB')

    def add_depth_of_field(
        self,
        image: Image.Image,
        focus_center: Tuple[int, int],
        focus_range: float = 0.6
    ) -> Image.Image:
        """
        Simula depth of field (profundidade de campo)

        Args:
            image: Imagem de entrada
            focus_center: Centro do foco (x, y)
            focus_range: Alcance do foco (0-1)

        Returns:
            Imagem com DoF
        """
        if not self.effects_config.get('depth_of_field', {}).get('enabled', False):
            return image

        width, height = image.size
        cx, cy = focus_center

        # Criar máscara de foco
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)

        # Gradiente radial de foco
        max_distance = math.sqrt(width**2 + height**2) / 2
        focus_radius = max_distance * focus_range

        for y in range(height):
            for x in range(width):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)

                if dist < focus_radius:
                    focus_val = 255
                else:
                    focus_val = max(0, int(255 * (1 - (dist - focus_radius) / max_distance)))

                mask.putpixel((x, y), focus_val)

        # Aplicar blur seletivo
        blurred = image.filter(ImageFilter.GaussianBlur(radius=8))

        # Composite usando máscara
        result = Image.composite(image, blurred, mask)

        return result

    def add_chromatic_aberration(
        self,
        image: Image.Image,
        strength: float = 2.0
    ) -> Image.Image:
        """
        Adiciona aberração cromática para efeito cinematográfico

        Args:
            image: Imagem de entrada
            strength: Força do efeito

        Returns:
            Imagem com aberração
        """
        if image.mode != 'RGB':
            image = image.convert('RGB')

        r, g, b = image.split()

        # Offset para cada canal
        offset = int(strength)

        # Criar imagem deslocada para cada canal
        r_shifted = Image.new('L', image.size)
        g_shifted = Image.new('L', image.size)
        b_shifted = Image.new('L', image.size)

        # Red - deslocar para esquerda
        r_shifted.paste(r, (-offset, 0))

        # Green - manter no centro
        g_shifted.paste(g, (0, 0))

        # Blue - deslocar para direita
        b_shifted.paste(b, (offset, 0))

        # Recombinar
        result = Image.merge('RGB', (r_shifted, g_shifted, b_shifted))

        return result

    def apply_all_effects(
        self,
        image: Image.Image,
        frame_number: int
    ) -> Image.Image:
        """
        Aplica todos os efeitos habilitados

        Args:
            image: Imagem de entrada
            frame_number: Número do frame atual

        Returns:
            Imagem com todos os efeitos
        """
        result = image.copy()

        # Atualizar e renderizar partículas
        if frame_number == 0:
            self.initialize_particles(image.width, image.height)

        self.update_particles(image.width, image.height)
        result = self.render_particles(result)

        # Aplicar glow cósmico
        result = self.apply_cosmic_glow(result)

        # Depth of field (opcional)
        if self.effects_config.get('depth_of_field', {}).get('enabled', False):
            center = (image.width // 2, image.height // 2)
            result = self.add_depth_of_field(result, center)

        return result
