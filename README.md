# AI Character Animator

Pipeline completo para gerar animações cinematográficas utilizando modelos de difusão via ComfyUI / AnimateDiff / Flux / ControlNet. O objetivo deste README é ser um guia de **primeiros passos**, conduzindo da configuração inicial até a renderização do primeiro vídeo.

## 🗺️ Roteiro de Primeiros Passos

1. [Antes de começar](#-antes-de-começar)
2. [Preparar o ambiente](#-preparar-o-ambiente)
3. [Executar a API](#-executar-a-api)
4. [Disparar a primeira cena](#-disparar-a-primeira-cena)
5. [Renderizar o vídeo](#-renderizar-o-vídeo)
6. [Próximos passos e automação](#-próximos-passos-e-automação)

As seções seguintes trazem detalhes complementares sobre a estrutura do projeto, scripts utilitários e critérios de aceite.

## 🔍 Antes de começar

- **Python 3.11+** instalado localmente (ou use o container Docker fornecido).
- **FFmpeg** disponível no `PATH` para compilar os vídeos.
- (Opcional) **ComfyUI CLI** configurado se desejar substituir o stub de geração por integração real.
- GPU com suporte CUDA recomendada para geração com modelos pesados.

## 🛠️ Preparar o ambiente

1. **Clonar o repositório**
   ```bash
   git clone <url-do-repo> ai_character_animator
   cd ai_character_animator
   ```

2. **Configurar variáveis de ambiente**
   ```bash
   cp .env.example .env
   ```
   Ajuste os caminhos conforme necessário:
   - `COMFYUI_CLI`: caminho do script principal da ComfyUI.
   - `MODEL_PATH`: diretório com os modelos SDXL customizados.
   - `OUTPUT_DIR`: base para armazenar frames e artefatos temporários.
   - `FFMPEG_BIN`: binário do FFmpeg (ex.: `/usr/bin/ffmpeg`).

3. **Instalar dependências com Make**
   ```bash
   make setup
   ```
   O alvo cria o ambiente virtual `.venv` e instala as dependências do `requirements.txt`.

> 💡 Prefere container? Pule para [Execução com Docker](#-execução-com-docker).

## 🚀 Executar a API

Inicie o servidor FastAPI/uvicorn:

```bash
make run
```

A API fica disponível em `http://localhost:8000`. A documentação automática pode ser acessada em `http://localhost:8000/docs`.

## 🎬 Disparar a primeira cena

1. **Selecionar um prompt** – Há um exemplo completo em `assets/prompts/example_scene.json`.
2. **Criar job de geração**
   ```bash
   curl -X POST http://localhost:8000/generate \
     -H "Content-Type: application/json" \
     -d @assets/prompts/example_scene.json
   ```
   O endpoint retorna um `job_id`. Enquanto a integração com ComfyUI não estiver ativa, frames dummy são produzidos.

3. **Acompanhar status**
   ```bash
   curl http://localhost:8000/status/<job_id>
   ```
   Estados possíveis: `pending`, `generating`, `frames_ready`, `rendering`, `completed`, `failed`.

## 🎞️ Renderizar o vídeo

Quando os frames estiverem prontos (`frames_ready`), dispare a renderização:

```bash
curl -X POST http://localhost:8000/render/<job_id>
```

O vídeo final 1080x1920@30fps é salvo em `final_renders/` utilizando o preset definido em `config/config.yaml`. O processo chama `scripts/render_ffmpeg.py`, que por sua vez utiliza o comando FFmpeg configurado.

> ✅ Para executar geração + pós-processamento + renderização em um único passo, utilize `POST /run_all` com o mesmo JSON da cena.

## 🔄 Próximos passos e automação

- **Executar todos os prompts de uma pasta** – armazene JSONs em `assets/prompts/` e itere chamando o endpoint `/generate` (ou use `/run_all`).
- **Integração com n8n** – configure nós HTTP para acionar `/generate`, monitorar `/status/{job_id}` e finalizar com `/render/{job_id}`.
- **Ativar ComfyUI real** – edite `.env` e `config/config.yaml` para apontar para seus modelos, ajustando parâmetros no script `scripts/generate_frames_comfy.py`.

## 🧱 Estrutura do projeto

```
assets/
  prompts/
  frames/
  outputs/
  logos/
  depth/
final_renders/
config/
app/
scripts/
models/
tests/
```

- `app/main.py`: API FastAPI com endpoints `/generate`, `/status`, `/render`, `/run_all`.
- `app/schemas.py`: modelos Pydantic para requests/responses.
- `app/utils.py`: helpers para diretórios, slugs, seeds e carregamento de configuração.
- `scripts/`: rotinas de geração, pós-processamento e renderização.
- `config/config.yaml`: presets de render (fps, resolução, CRF, efeitos).
- `assets/prompts/`: cenas de exemplo (entrada JSON).

## 🧰 Scripts principais

- `scripts/generate_frames_comfy.py` – integra ComfyUI/AnimateDiff (gera frames sintéticos quando ComfyUI não está disponível).
- `scripts/postprocess.py` – aplica color grade, blur, glow, depth e glitches usando OpenCV/Numpy.
- `scripts/render_ffmpeg.py` – monta o vídeo final com FFmpeg, adicionando logos e transições simples.

## 🧪 Testes

Execute os testes de fumaça com:

```bash
make test
```

O teste `tests/test_api_smoke.py` valida o ciclo básico de geração e renderização com as dependências stub.

## 🐳 Execução com Docker

```bash
docker compose up -d --build
```

O serviço sobe com as variáveis de ambiente definidas e fica acessível em `http://localhost:8000`.

## ✅ Critérios de aceite

- Pipeline executa com `make setup && make run` ou `docker compose up -d`.
- `POST /generate` cria frames dummy quando ComfyUI não está configurado.
- `POST /render` produz um MP4 válido em `final_renders/`.
- Código modular, pronto para substituir stubs por integrações reais.

## 📄 Licença

MIT
