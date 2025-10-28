# Guia de Modelos Locais 🤖

Sistema completo para usar modelos Hugging Face localmente, sem depender de APIs externas!

## 🌟 Vantagens dos Modelos Locais

✅ **Sem custos de API** - Tudo roda localmente
✅ **Maior consistência** - ControlNet garante personagem idêntico
✅ **Mais rápido** - RTX 4070 processa em segundos
✅ **Offline** - Funciona sem internet (após download)
✅ **Customizável** - Ajuste fino completo
✅ **Privacidade** - Suas imagens não saem da máquina

## 📦 Modelos Recomendados

### Setup Mínimo (~8GB)

Para começar, baixe este conjunto básico:

```bash
python scripts/download_models.py --minimal
```

Inclui:
- **Realistic Vision V5.1** - Modelo SD para personagens realistas
- **ControlNet Canny** - Mantém estrutura da imagem
- **AnimateDiff Motion Module** - Para animações suaves

### Setup Completo (~25GB)

Para máxima qualidade:

```bash
python scripts/download_models.py --full
```

Inclui todos os modelos + SDXL e upscalers.

## 🚀 Instalação

### 1. Instalar Dependências

```bash
# Instalar bibliotecas Hugging Face
pip install diffusers transformers accelerate safetensors

# xformers (otimização de memória GPU)
pip install xformers

# Para interpolação RIFE (opcional)
pip install rife-ncnn-vulkan-python
```

### 2. Download de Modelos

#### Opção A: Setup Automático (Recomendado)

```bash
# Setup mínimo (8GB)
python scripts/download_models.py --minimal

# Setup completo (25GB)
python scripts/download_models.py --full
```

#### Opção B: Download Seletivo

```bash
# Listar modelos disponíveis
python scripts/download_models.py --list

# Baixar categoria específica
python scripts/download_models.py --category stable_diffusion

# Baixar modelo específico
python scripts/download_models.py --model SG161222/Realistic_Vision_V5.1_noVAE
```

### 3. Configurar

Edite `config/config.yaml`:

```yaml
local_models:
  enabled: true  # Ativar modelos locais
  models_dir: "models"

  generator:
    method: "img2img"  # ou "controlnet" ou "animatediff"
    use_controlnet: true  # Recomendado para consistência

  interpolation:
    method: "rife"  # Melhor qualidade
```

## 🎯 Uso

### Modo Básico

```bash
# Usar modelos locais (configuração no config.yaml)
python scripts/hybrid_animator.py assets/input/fiza.png

# Forçar uso de modelos locais
python scripts/hybrid_animator.py assets/input/fiza.png --use-local

# Forçar uso de API Gemini
python scripts/hybrid_animator.py assets/input/fiza.png --use-api
```

### Modos de Geração

#### 1. Img2Img (Rápido, boa qualidade)

```yaml
generator:
  method: "img2img"
  use_controlnet: false
```

**Prós**: Rápido, bom para variações sutis
**Contras**: Menos controle sobre estrutura
**Tempo**: ~0.5s por frame (RTX 4070)

#### 2. ControlNet (Melhor consistência)

```yaml
generator:
  method: "controlnet"
  use_controlnet: true
  controlnet_type: "canny"  # ou "depth" ou "tile"
```

**Prós**: Máxima consistência, mantém exatamente a estrutura
**Contras**: Ligeiramente mais lento
**Tempo**: ~1s por frame (RTX 4070)
**Recomendado**: ✅ Para personagens

#### 3. AnimateDiff (Mais frames de uma vez)

```yaml
generator:
  method: "animatediff"

animatediff:
  enabled: true
  num_frames: 16  # Múltiplo de 8
```

**Prós**: Gera sequências suaves automaticamente
**Contras**: Requer mais VRAM, menos controle
**Tempo**: ~5s para 16 frames (RTX 4070)

## ⚙️ Configuração Avançada

### Ajustar Qualidade vs Velocidade

```yaml
generation:
  strength: 0.3        # Menor = mais similar ao original
  guidance_scale: 7.5  # Maior = mais fiel ao prompt
  num_inference_steps: 30  # Mais steps = melhor qualidade
```

**Rápido** (20 steps):
```yaml
num_inference_steps: 20
guidance_scale: 6.0
```

**Balanceado** (30 steps):
```yaml
num_inference_steps: 30
guidance_scale: 7.5
```

**Qualidade Máxima** (50 steps):
```yaml
num_inference_steps: 50
guidance_scale: 8.5
```

### Escolher Tipo de Interpolação

```yaml
interpolation:
  method: "rife"  # rife, film, ou optical_flow
```

**RIFE**: ✅ Recomendado
- Melhor qualidade
- Rápido (~0.1s por frame)
- Requer modelo RIFE

**FILM**: Boa qualidade
- Similar ao RIFE
- Requer TensorFlow
- ~0.2s por frame

**Optical Flow**: Básico
- Não requer modelo
- Qualidade inferior
- Muito rápido

### Prompts Customizados

```yaml
prompts:
  base: |
    seu prompt personalizado aqui,
    descreva o estilo desejado

  negative: |
    coisas a evitar:
    blurry, low quality, deformed

  variations:
    - "primeira variação"
    - "segunda variação"
    - "terceira variação"
```

## 📊 Performance Esperada (RTX 4070)

### Img2Img
- Keyframe: ~0.5s
- 10 keyframes: ~5s
- Interpolação (RIFE): ~15s (150 frames)
- **Total 5s video**: ~30-40 segundos

### ControlNet
- Keyframe: ~1s
- 10 keyframes: ~10s
- Interpolação (RIFE): ~15s
- **Total 5s video**: ~40-50 segundos

### AnimateDiff
- 16 frames: ~5s
- Total com interpolação: ~20-30 segundos

**Comparação com API Gemini**: 5-10x mais rápido! 🚀

## 🎨 Modelos Disponíveis

### Stable Diffusion

#### Realistic Vision V5.1 ⭐ Recomendado
```yaml
model_name: "Realistic_Vision_V5.1_noVAE"
```
- Excelente para personagens
- Realista e consistente
- ~5GB

#### DreamShaper XL
```yaml
model_name: "dreamshaper-xl-1-0"
```
- SDXL - Alta resolução
- Muito versátil
- ~7GB

### ControlNet

#### Canny ⭐ Recomendado
```yaml
controlnet_type: "canny"
```
- Detecta bordas
- Mantém estrutura exata
- Melhor para personagens

#### Depth
```yaml
controlnet_type: "depth"
```
- Usa profundidade
- Bom para cenas 3D

#### Tile
```yaml
controlnet_type: "tile"
```
- Para upscaling
- Mantém detalhes

## 🔧 Troubleshooting

### Erro: "Out of Memory" (VRAM)

Reduza uso de memória:

```yaml
generation:
  num_inference_steps: 20  # Reduzir steps

processing:
  batch_size: 1  # Processar 1 por vez
```

Ou use CPU (mais lento):

```yaml
cuda:
  enabled: false
```

### Modelos não encontrados

```bash
# Verificar modelos instalados
ls models/stable_diffusion/

# Re-baixar
python scripts/download_models.py --minimal
```

### xformers não instala

xformers requer compilação. Se falhar:

```bash
# Desabilitar no código ou continuar sem
# Pipeline funciona sem xformers, só usa mais memória
```

### Qualidade ruim

Ajustar parâmetros:

```yaml
generation:
  strength: 0.2  # Menos transformação
  guidance_scale: 8.5  # Mais fidelidade ao prompt
  num_inference_steps: 50  # Mais qualidade
```

## 💡 Dicas Pro

### 1. Usar ControlNet para Consistência Perfeita

```yaml
generator:
  method: "controlnet"
  use_controlnet: true
  controlnet_type: "canny"
```

### 2. Combinar Múltiplos Métodos

```python
# Gerar keyframes com ControlNet
keyframes = animator.generate_keyframes(image, method="controlnet")

# Interpolar com RIFE
frames = animator.interpolate_frames(keyframes, method="rife")
```

### 3. Ajuste Fino de Prompts

Seja específico:
```
Bom: "cosmic scene, character, stars"
Melhor: "cosmic scene, space explorer character Fiza,
         ethereal glow, vibrant purple and blue nebula,
         professional digital art, highly detailed"
```

### 4. Processar em Lote

```bash
# Processar múltiplas imagens
for img in assets/input/*.png; do
    python scripts/hybrid_animator.py "$img" --use-local
done
```

### 5. Monitorar VRAM

```python
from model_manager import ModelManager

mm = ModelManager()
print(mm.get_memory_usage())
# {'allocated_gb': 4.2, 'total_gb': 12.0, 'free_gb': 7.8}
```

## 📈 Comparação: Local vs API

| Aspecto | Modelos Locais | API Gemini |
|---------|---------------|------------|
| Velocidade | ⚡⚡⚡ Muito rápido | 🐌 Lento |
| Custo | ✅ Grátis | 💰 Pago por uso |
| Qualidade | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Consistência | ✅ Perfeita (ControlNet) | ⚠️ Variável |
| Offline | ✅ Sim | ❌ Não |
| Setup | 📦 ~8GB download | ⚡ Instant |
| GPU | 🎮 Requer | ❌ Não precisa |

## 🎯 Receitas Prontas

### Máxima Qualidade (Slow)

```yaml
local_models:
  enabled: true

  generator:
    method: "controlnet"
    controlnet_type: "canny"

  generation:
    strength: 0.25
    guidance_scale: 8.5
    num_inference_steps: 50
    scheduler: "DPMSolver"

  interpolation:
    method: "rife"
```

### Balanceado (Recomendado)

```yaml
local_models:
  enabled: true

  generator:
    method: "controlnet"
    controlnet_type: "canny"

  generation:
    strength: 0.3
    guidance_scale: 7.5
    num_inference_steps: 30

  interpolation:
    method: "rife"
```

### Rápido (Fast)

```yaml
local_models:
  enabled: true

  generator:
    method: "img2img"
    use_controlnet: false

  generation:
    strength: 0.35
    guidance_scale: 6.5
    num_inference_steps: 20

  interpolation:
    method: "optical_flow"
```

## 📚 Recursos Adicionais

- [Diffusers Docs](https://huggingface.co/docs/diffusers)
- [ControlNet Paper](https://arxiv.org/abs/2302.05543)
- [AnimateDiff](https://github.com/guoyww/AnimateDiff)
- [RIFE](https://github.com/megvii-research/ECCV2022-RIFE)

---

**Pronto para criar animações incríveis com modelos locais! 🚀✨**
