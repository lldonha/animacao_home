# 🚀 Guia de Instalação - Fiza Cosmic Animator

Guia completo para instalar e configurar o sistema de animação da Fiza.

---

## 📋 Requisitos do Sistema

### Hardware Mínimo
- **CPU**: Intel i5 / AMD Ryzen 5 ou superior
- **RAM**: 16GB (32GB recomendado)
- **GPU**: NVIDIA RTX 3060 ou superior (RTX 4070 recomendada)
- **VRAM**: 8GB mínimo (12GB recomendado)
- **Armazenamento**: 50GB livres (para modelos e outputs)

### Software Necessário
- **OS**: Linux (Ubuntu 20.04+) / Windows 10+ / macOS 11+
- **Python**: 3.9 ou superior
- **CUDA**: 12.x (para GPU NVIDIA)
- **Git**: Para clonar o repositório
- **FFmpeg**: Para renderização de vídeo

---

## 🔧 Instalação Passo a Passo

### 1️⃣ Verificar Pré-requisitos

#### Verificar Python
```bash
python3 --version
# Deve retornar: Python 3.9.x ou superior

# Se não tiver Python instalado:
# Ubuntu/Debian:
sudo apt update
sudo apt install python3 python3-pip python3-venv

# macOS:
brew install python@3.9

# Windows: Baixar de python.org
```

#### Verificar CUDA (Opcional, mas recomendado)
```bash
nvidia-smi
# Deve mostrar informações da sua GPU

# Se não funcionar, instalar CUDA:
# https://developer.nvidia.com/cuda-downloads
```

#### Verificar FFmpeg
```bash
ffmpeg -version

# Se não tiver instalado:
# Ubuntu/Debian:
sudo apt install ffmpeg

# macOS:
brew install ffmpeg

# Windows: Baixar de ffmpeg.org
```

---

### 2️⃣ Clonar o Repositório

```bash
# Ir para diretório desejado
cd /home/user/  # ou seu diretório preferido

# Clonar (se ainda não clonou)
git clone <seu-repositorio-url> animacao_home
cd animacao_home

# Verificar branch
git branch
```

---

### 3️⃣ Criar Ambiente Virtual

```bash
# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Você verá (venv) no prompt
```

---

### 4️⃣ Instalar Dependências

#### Método 1: Instalação Automática (Recomendado)
```bash
./setup.sh

# Aguarde... (pode demorar 5-10 minutos)
```

#### Método 2: Instalação Manual
```bash
# Atualizar pip
pip install --upgrade pip

# Instalar dependências principais
pip install -r requirements.txt

# Instalar PyTorch com CUDA (GPU)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# OU PyTorch sem CUDA (CPU only)
pip install torch torchvision

# Instalar dependências Hugging Face
pip install diffusers transformers accelerate safetensors huggingface-hub

# Instalar xformers (otimização GPU - opcional)
pip install xformers
```

---

### 5️⃣ Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar arquivo
nano .env  # ou vim, ou qualquer editor

# Adicionar no .env:
GEMINI_API_KEY=sua_chave_aqui  # Opcional se usar modelos locais
```

**Obter chave Gemini** (opcional): https://makersuite.google.com/app/apikey

---

### 6️⃣ Baixar Modelos (Escolha uma opção)

#### Opção A: Setup Mínimo (~8GB) ⭐ Recomendado
```bash
python scripts/download_models.py --minimal
```

**Inclui**:
- Realistic Vision V5.1 (~5GB)
- ControlNet Canny (~1.5GB)
- AnimateDiff Motion Module (~1.8GB)

**Tempo de download**: 20-40 minutos (depende da internet)

#### Opção B: Setup Completo (~25GB)
```bash
python scripts/download_models.py --full
```

**Inclui**:
- Todos os modelos do setup mínimo
- DreamShaper XL (~7GB)
- ControlNet adicional (~3GB)
- Real-ESRGAN (~200MB)
- Modelos extras

**Tempo de download**: 1-2 horas

#### Opção C: Não Baixar Modelos (Usar API Gemini)
```bash
# Pular este passo
# Configure GEMINI_API_KEY no .env
# Use flag --use-api ao animar
```

---

### 7️⃣ Verificar Instalação

```bash
# Testar imports
python -c "
import torch
import diffusers
import PIL
import cv2
print('✓ Todos os imports OK!')
print(f'CUDA disponível: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
"
```

**Saída esperada**:
```
✓ Todos os imports OK!
CUDA disponível: True
GPU: NVIDIA GeForce RTX 4070
```

---

## ✅ Teste de Instalação

### Teste Básico (Sem Modelos)

```bash
# Criar imagem de teste
python -c "
from PIL import Image, ImageDraw
img = Image.new('RGB', (1024, 1024), color=(50, 50, 100))
draw = ImageDraw.Draw(img)
draw.ellipse([312, 312, 712, 712], fill=(200, 150, 255))
img.save('assets/input/test.png')
print('✓ Imagem de teste criada')
"

# Testar componentes
python -c "
from scripts.effects_generator import CosmicEffectsGenerator
from scripts.cuda_processor import CUDAImageProcessor
from PIL import Image
import yaml

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

effects = CosmicEffectsGenerator(config)
cuda = CUDAImageProcessor()

img = Image.open('assets/input/test.png')
result = effects.apply_all_effects(img, 0)
result.save('assets/output/test_effects.png')

print('✓ Teste de efeitos OK!')
print(f'✓ CUDA: {cuda.use_cuda}')
"
```

### Teste Completo (Com Modelos Locais)

```bash
# Animar imagem de teste
python scripts/hybrid_animator.py assets/input/test.png \
  --output assets/output/test \
  --name test_animation \
  --use-local

# Verificar saída
ls -lh assets/output/test/
# Deve mostrar: test_animation_9x16.mp4, test_animation_16x9.mp4, etc.
```

### Teste com API Gemini

```bash
python scripts/hybrid_animator.py assets/input/test.png \
  --output assets/output/test_gemini \
  --name test_gemini \
  --use-api
```

---

## 🔧 Configuração Adicional

### Configurar GPU (Opcional)

```bash
# Verificar CUDA
nvidia-smi

# Configurar device ID (se múltiplas GPUs)
nano config/config.yaml

# Editar:
cuda:
  device_id: 0  # 0 = primeira GPU, 1 = segunda, etc.
  enabled: true
  memory_fraction: 0.8
```

### Configurar n8n (Opcional)

```bash
# Instalar n8n
npm install -g n8n

# Iniciar n8n
n8n start

# Acessar: http://localhost:5678
# Importar workflows de: workflows/*.json
```

### Otimizar Configurações

```bash
# Editar configurações
nano config/config.yaml

# Para máxima velocidade:
local_models:
  generator:
    method: "img2img"
  generation:
    num_inference_steps: 20

# Para máxima qualidade:
local_models:
  generator:
    method: "controlnet"
  generation:
    num_inference_steps: 50
```

---

## 📦 Estrutura Pós-Instalação

```
animacao_home/
├── venv/                    # ✓ Ambiente virtual
├── models/                  # ✓ Modelos baixados
│   ├── stable_diffusion/
│   ├── controlnet/
│   └── animation/
├── assets/
│   ├── input/              # 👈 Coloque suas imagens aqui
│   ├── output/             # 👈 Vídeos gerados aqui
│   └── temp/
├── scripts/                # ✓ Scripts Python
├── config/
│   └── config.yaml         # ✓ Configurado
├── .env                    # ✓ Variáveis de ambiente
└── requirements.txt
```

---

## 🚀 Uso Rápido Pós-Instalação

```bash
# 1. Ativar ambiente virtual
source venv/bin/activate

# 2. Adicionar imagem
cp sua_imagem.png assets/input/

# 3. Animar
python scripts/hybrid_animator.py assets/input/sua_imagem.png

# 4. Ver resultado
ls assets/output/
```

---

## 🐛 Troubleshooting

### Problema: `pip: command not found`

```bash
# Ubuntu/Debian
sudo apt install python3-pip

# macOS
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py

# Windows
# Reinstalar Python de python.org com opção "Add to PATH"
```

### Problema: `CUDA not available`

```bash
# Verificar driver NVIDIA
nvidia-smi

# Se não funcionar:
# 1. Instalar drivers NVIDIA: https://www.nvidia.com/drivers
# 2. Instalar CUDA Toolkit: https://developer.nvidia.com/cuda-downloads

# Reinstalar PyTorch com CUDA
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Verificar novamente
python -c "import torch; print(torch.cuda.is_available())"
```

### Problema: `xformers` não instala

```bash
# xformers é opcional, continuar sem ele:
pip install -r requirements.txt --no-deps
pip install torch torchvision diffusers transformers

# OU compilar do source (avançado):
pip install ninja
pip install -v -U git+https://github.com/facebookresearch/xformers.git@main#egg=xformers
```

### Problema: `Out of Memory` durante download

```bash
# Baixar modelos um por um
python scripts/download_models.py --category stable_diffusion
python scripts/download_models.py --category controlnet
python scripts/download_models.py --category animation
```

### Problema: FFmpeg não encontrado

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 1. Baixar: https://ffmpeg.org/download.html
# 2. Extrair para C:\ffmpeg
# 3. Adicionar ao PATH: C:\ffmpeg\bin

# Verificar
ffmpeg -version
```

### Problema: Modelos muito lentos para baixar

```bash
# Usar mirror Hugging Face (China/Asia)
export HF_ENDPOINT=https://hf-mirror.com
python scripts/download_models.py --minimal

# OU baixar apenas o essencial
python scripts/download_models.py \
  --model SG161222/Realistic_Vision_V5.1_noVAE
```

### Problema: `Permission denied` ao executar setup.sh

```bash
chmod +x setup.sh
./setup.sh
```

---

## 📊 Checklist de Instalação

- [ ] Python 3.9+ instalado
- [ ] Git instalado
- [ ] Repositório clonado
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] PyTorch instalado (com ou sem CUDA)
- [ ] FFmpeg instalado
- [ ] Arquivo `.env` configurado (se usar API)
- [ ] Modelos baixados (se usar local) OU API key configurada
- [ ] Teste básico executado com sucesso
- [ ] Primeira animação gerada

---

## ⏱️ Tempo Total de Instalação

| Etapa | Tempo Estimado |
|-------|---------------|
| Instalar pré-requisitos | 10-15 min |
| Clonar repo e criar venv | 2 min |
| Instalar dependências | 5-10 min |
| Configurar .env | 1 min |
| Download modelos (mínimo) | 20-40 min |
| Testes | 5 min |
| **TOTAL (Setup Mínimo)** | **40-75 min** |
| **TOTAL (Setup Completo)** | **1.5-2 horas** |

---

## 🎯 Próximos Passos

Após instalação completa:

1. **Ler documentação**:
   ```bash
   cat README.md
   cat docs/QUICKSTART.md
   cat docs/LOCAL_MODELS_GUIDE.md
   ```

2. **Criar primeira animação**:
   ```bash
   python scripts/hybrid_animator.py assets/input/sua_imagem.png
   ```

3. **Explorar configurações**:
   ```bash
   nano config/config.yaml
   ```

4. **Experimentar diferentes modos**:
   ```bash
   # Modelos locais
   python scripts/hybrid_animator.py imagem.png --use-local

   # API Gemini
   python scripts/hybrid_animator.py imagem.png --use-api
   ```

---

## 📞 Suporte

### Comandos Úteis

```bash
# Ver ajuda do animador
python scripts/hybrid_animator.py --help

# Ver ajuda do download
python scripts/download_models.py --help

# Listar modelos disponíveis
python scripts/download_models.py --list

# Ver versões instaladas
pip list | grep -E "(torch|diffusers|transformers)"

# Verificar uso de GPU
nvidia-smi

# Limpar cache
rm -rf assets/temp/*
```

### Logs e Debugging

```bash
# Executar com mais verbose
python scripts/hybrid_animator.py imagem.png -v

# Ver logs completos
python scripts/hybrid_animator.py imagem.png 2>&1 | tee animation.log
```

---

## 🌟 Instalação Bem-Sucedida!

Se chegou até aqui, seu sistema está pronto! 🎉

**Teste final**:
```bash
python scripts/hybrid_animator.py assets/input/test.png
ls assets/output/
```

**Próximo passo**: Criar sua primeira animação da Fiza! 🚀✨

---

**Documentação Relacionada**:
- [README.md](README.md) - Documentação completa
- [QUICKSTART.md](docs/QUICKSTART.md) - Guia de uso rápido
- [LOCAL_MODELS_GUIDE.md](docs/LOCAL_MODELS_GUIDE.md) - Guia de modelos locais

**Desenvolvido com ❤️ para Fiza, a Exploradora Cósmica**
