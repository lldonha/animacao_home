# Fiza - Exploradora Cósmica | Cosmic Animator ✨🚀

Sistema de animação de última geração para criar vídeos cósmicos impressionantes usando Gemini AI, CUDA e n8n.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![CUDA](https://img.shields.io/badge/CUDA-12.x-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🌟 Características

- **IA Generativa**: Usa Google Gemini para gerar variações de frames com estilo consistente
- **Aceleração GPU**: Processamento CUDA otimizado para RTX 4070
- **Efeitos Cósmicos**: Partículas, glow, motion blur e mais
- **Múltiplos Formatos**: Gera automaticamente vídeos 9:16 (shorts) e 16:9 (horizontal)
- **Stop Motion AI**: Interpolação inteligente entre keyframes
- **Automação n8n**: Workflows completos para processamento em lote
- **API REST**: Integração fácil com outros sistemas

## 🎬 Funcionalidades

### Efeitos Visuais
- ✨ Partículas cósmicas animadas
- 🌟 Glow e brilho etéreo
- 🎨 Aberração cromática
- 🌊 Motion blur dinâmico
- 🔍 Depth of field
- 💫 Lens flare

### Formatos de Saída
- 📱 **9:16** (1080x1920) - Perfeito para TikTok, Instagram Reels, YouTube Shorts
- 🖥️ **16:9** (1920x1080) - Ideal para YouTube, vídeos horizontais
- 🎞️ Preview GIF para rápida visualização

### Automação
- 🤖 Processamento em lote via n8n
- ⏰ Agendamento automático
- 📊 Monitoramento de status em tempo real
- 🔔 Notificações de conclusão

## 🚀 Instalação

### Pré-requisitos

- Python 3.9+
- NVIDIA GPU com CUDA 12.x (RTX 4070 ou superior recomendado)
- FFmpeg com suporte NVENC
- n8n (opcional, para automação)

### 1. Clonar e Configurar

```bash
# Clonar repositório
git clone <seu-repositorio>
cd animacao_home

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar API Keys

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env e adicionar sua chave
nano .env
```

Adicione sua chave do Gemini:
```env
GEMINI_API_KEY=sua_chave_aqui
```

Para obter uma chave: https://makersuite.google.com/app/apikey

### 3. Verificar CUDA

```bash
# Verificar se CUDA está disponível
python -c "import torch; print(f'CUDA disponível: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
```

## 📖 Uso

### Modo Básico (CLI)

```bash
# Animar uma imagem
python scripts/main.py assets/input/fiza_base.png

# Com configurações personalizadas
python scripts/main.py assets/input/fiza_base.png --output assets/output/teste --name fiza_v1

# Com arquivo de configuração customizado
python scripts/main.py assets/input/fiza_base.png --config config/custom.yaml
```

### Modo API Server

```bash
# Iniciar servidor
python scripts/api_server.py

# Em outro terminal, testar
curl -X POST http://localhost:8000/api/animate \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "assets/input/fiza_base.png",
    "output_dir": "assets/output",
    "base_name": "fiza_animation"
  }'

# Verificar status
curl http://localhost:8000/api/status/<job_id>
```

### Upload via API

```bash
# Upload de imagem
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/caminho/para/imagem.png"

# Usar caminho retornado para animar
curl -X POST http://localhost:8000/api/animate \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "<caminho_retornado>"
  }'
```

## 🔧 Configuração Avançada

### Arquivo config.yaml

Customize todos os aspectos da animação:

```yaml
animation:
  fps: 30
  duration: 5

  effects:
    glow:
      enabled: true
      intensity: 0.8

    particles:
      enabled: true
      count: 200
      colors:
        - [255, 255, 200]  # Amarelo
        - [200, 150, 255]  # Roxo
        - [100, 200, 255]  # Azul

gemini:
  model: "gemini-2.0-flash-exp"
  generation:
    temperature: 0.9

cuda:
  enabled: true
  device_id: 0
```

### Personalizar Efeitos

```python
# Criar configuração customizada
from scripts.main import FizaAnimator

animator = FizaAnimator("config/config.yaml")

# Modificar configuração em runtime
animator.config['animation']['effects']['particles']['count'] = 500
animator.config['animation']['effects']['glow']['intensity'] = 1.0

# Animar
results = animator.animate("assets/input/fiza.png")
```

## 🤖 Integração com n8n

### 1. Instalar n8n

```bash
npm install -g n8n

# Iniciar n8n
n8n start
```

### 2. Importar Workflows

1. Acesse http://localhost:5678
2. Vá em **Workflows** → **Import**
3. Importe os arquivos da pasta `workflows/`:
   - `fiza_animator_main.json` - Workflow principal
   - `fiza_animator_batch.json` - Processamento em lote
   - `fiza_animator_scheduler.json` - Agendamento automático

### 3. Configurar Webhooks

Os workflows estão pré-configurados para se conectar ao servidor API em `http://localhost:8000`.

Se necessário, ajuste as URLs nos nós HTTP Request.

### 4. Usar Workflows

#### Workflow Principal (fiza_animator_main)

Trigger via webhook:
```bash
curl -X POST http://localhost:5678/webhook/fiza-animate \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "assets/input/fiza.png",
    "output_dir": "assets/output"
  }'
```

#### Workflow Batch (fiza_animator_batch)

Processar múltiplas imagens:
```bash
curl -X POST http://localhost:5678/webhook/fiza-batch \
  -H "Content-Type: application/json" \
  -d '{
    "image_paths": [
      "assets/input/fiza1.png",
      "assets/input/fiza2.png",
      "assets/input/fiza3.png"
    ]
  }'
```

#### Workflow Scheduler (fiza_animator_scheduler)

Este workflow executa automaticamente:
- Por padrão: todos os dias às 9h
- Processa todas as imagens em `assets/input`
- Salva resultados em `assets/output/scheduled`

Para ativar:
1. Abra o workflow no n8n
2. Clique em **Active** no canto superior direito

## 📊 Estrutura do Projeto

```
animacao_home/
├── assets/
│   ├── input/          # Imagens de entrada
│   ├── output/         # Vídeos gerados
│   └── temp/           # Arquivos temporários
├── config/
│   └── config.yaml     # Configuração principal
├── scripts/
│   ├── main.py         # Pipeline principal
│   ├── gemini_api.py   # Integração Gemini
│   ├── cuda_processor.py   # Processamento GPU
│   ├── effects_generator.py # Efeitos visuais
│   ├── video_renderer.py   # Renderização de vídeo
│   └── api_server.py   # Servidor API
├── workflows/
│   ├── fiza_animator_main.json
│   ├── fiza_animator_batch.json
│   └── fiza_animator_scheduler.json
├── docs/               # Documentação adicional
├── requirements.txt    # Dependências Python
├── .env.example        # Exemplo de variáveis de ambiente
└── README.md           # Este arquivo
```

## 🎨 Exemplos de Uso

### 1. Animação Simples

```bash
python scripts/main.py assets/input/fiza_cosmic.png
```

Output:
- `assets/output/fiza_cosmic_9x16.mp4` - Vertical (Short)
- `assets/output/fiza_cosmic_16x9.mp4` - Horizontal
- `assets/output/fiza_cosmic_preview.gif` - Preview animado

### 2. Animação com Muitas Partículas

```python
from scripts.main import FizaAnimator

animator = FizaAnimator()
animator.config['animation']['effects']['particles']['count'] = 500
animator.config['animation']['effects']['particles']['size_range'] = [3, 12]

results = animator.animate("assets/input/fiza.png")
```

### 3. Animação Rápida (3 segundos)

```yaml
# config/quick.yaml
animation:
  duration: 3
  fps: 24
```

```bash
python scripts/main.py assets/input/fiza.png --config config/quick.yaml
```

## 🐛 Troubleshooting

### CUDA não disponível

```bash
# Verificar instalação CUDA
nvidia-smi

# Reinstalar PyTorch com CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Erro de API Gemini

- Verifique se a chave está correta no `.env`
- Confirme que tem créditos disponíveis
- Teste a chave: https://aistudio.google.com/

### FFmpeg NVENC não disponível

```bash
# Verificar NVENC
ffmpeg -hide_banner -encoders | grep nvenc

# Instalar FFmpeg com NVENC (Ubuntu)
sudo apt install ffmpeg
```

### Falta de memória GPU

Ajuste no `config.yaml`:
```yaml
cuda:
  memory_fraction: 0.6  # Reduzir de 0.8 para 0.6

processing:
  batch_size: 2  # Reduzir tamanho do batch
```

## 🔬 Desenvolvimento

### Executar Testes

```bash
# Instalar dependências de dev
pip install pytest pytest-cov

# Executar testes
pytest tests/

# Com cobertura
pytest --cov=scripts tests/
```

### Adicionar Novos Efeitos

1. Edite `scripts/effects_generator.py`
2. Adicione seu método:

```python
def add_custom_effect(self, image: Image.Image) -> Image.Image:
    # Seu efeito aqui
    return processed_image
```

3. Integre em `apply_all_effects`:

```python
def apply_all_effects(self, image, frame_number):
    result = image.copy()
    # ...
    result = self.add_custom_effect(result)
    return result
```

## 📈 Performance

### Benchmarks (RTX 4070)

- Geração de keyframe (Gemini): ~3-5s por frame
- Interpolação (optical flow): ~0.1s por frame
- Aplicação de efeitos: ~0.05s por frame
- Renderização de vídeo (NVENC): ~2-3s por vídeo

**Tempo total** (5s @ 30fps = 150 frames):
- Com 10 keyframes: ~3-5 minutos
- Com 5 keyframes: ~2-3 minutos

### Otimizações

Para processamento mais rápido:

```yaml
# config/fast.yaml
animation:
  fps: 24  # Reduzir de 30
  duration: 4  # Reduzir de 5

gemini:
  stop_motion:
    frames_between_generations: 10  # Aumentar

processing:
  batch_size: 8  # Aumentar (se tiver VRAM)
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🙏 Agradecimentos

- Google Gemini pela incrível API de IA generativa
- NVIDIA pelos drivers CUDA
- Comunidade n8n pela plataforma de automação
- Comunidade PyTorch e OpenCV

## 📞 Suporte

- Issues: [GitHub Issues](seu-link-aqui)
- Documentação: [Wiki](seu-link-aqui)
- Email: seu-email@exemplo.com

---

Feito com ❤️ para Fiza, a Exploradora Cósmica 🚀✨
