"""
API Server para integração com n8n
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
from pathlib import Path
import yaml
import logging
import uuid
import json
from datetime import datetime
import asyncio

from main import FizaAnimator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fiza Cosmic Animator API",
    description="API para animação da Fiza - Exploradora Cósmica",
    version="1.0.0"
)

# Armazenar jobs em memória (em produção, usar Redis ou banco de dados)
jobs_db: Dict[str, Dict[str, Any]] = {}


class AnimationRequest(BaseModel):
    """Request para criar animação"""
    image_path: str
    output_dir: Optional[str] = "assets/output"
    base_name: Optional[str] = None
    config_overrides: Optional[Dict[str, Any]] = None


class AnimationStatus(BaseModel):
    """Status de um job de animação"""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: float  # 0-100
    message: str
    started_at: str
    completed_at: Optional[str] = None
    results: Optional[Dict[str, str]] = None
    error: Optional[str] = None


class BatchRequest(BaseModel):
    """Request para processar múltiplas imagens"""
    image_paths: List[str]
    output_dir: Optional[str] = "assets/output"
    config_overrides: Optional[Dict[str, Any]] = None


def update_job_status(
    job_id: str,
    status: str,
    progress: float = 0,
    message: str = "",
    results: Optional[Dict[str, str]] = None,
    error: Optional[str] = None
):
    """Atualiza status de um job"""
    if job_id in jobs_db:
        jobs_db[job_id].update({
            'status': status,
            'progress': progress,
            'message': message,
            'results': results,
            'error': error
        })

        if status in ['completed', 'failed']:
            jobs_db[job_id]['completed_at'] = datetime.now().isoformat()


async def process_animation(
    job_id: str,
    request: AnimationRequest,
    config_path: str = "config/config.yaml"
):
    """Processa animação em background"""
    try:
        update_job_status(job_id, 'processing', 0, 'Inicializando...')

        # Carregar configuração
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Aplicar overrides se fornecidos
        if request.config_overrides:
            config.update(request.config_overrides)

        # Criar animador
        update_job_status(job_id, 'processing', 10, 'Criando animador...')
        animator = FizaAnimator(config_path)

        # Verificar se imagem existe
        if not Path(request.image_path).exists():
            raise FileNotFoundError(f"Imagem não encontrada: {request.image_path}")

        # Executar animação
        update_job_status(job_id, 'processing', 20, 'Carregando imagem base...')

        results = animator.animate(
            image_path=request.image_path,
            output_dir=request.output_dir or "assets/output",
            base_name=request.base_name
        )

        # Converter Path para string
        results_str = {k: str(v) for k, v in results.items()}

        # Marcar como completo
        update_job_status(
            job_id,
            'completed',
            100,
            'Animação concluída com sucesso!',
            results=results_str
        )

    except Exception as e:
        logger.error(f"Erro no job {job_id}: {e}", exc_info=True)
        update_job_status(
            job_id,
            'failed',
            0,
            'Erro durante processamento',
            error=str(e)
        )


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "name": "Fiza Cosmic Animator API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


@app.post("/api/animate")
async def create_animation(
    request: AnimationRequest,
    background_tasks: BackgroundTasks
):
    """
    Cria uma nova animação

    Returns:
        Job ID para acompanhamento
    """
    try:
        # Gerar ID único para o job
        job_id = str(uuid.uuid4())

        # Criar job
        jobs_db[job_id] = {
            'job_id': job_id,
            'status': 'pending',
            'progress': 0,
            'message': 'Job criado',
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'results': None,
            'error': None
        }

        # Adicionar job à fila de background
        background_tasks.add_task(process_animation, job_id, request)

        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Job criado com sucesso"
        }

    except Exception as e:
        logger.error(f"Erro ao criar job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Obtém status de um job

    Args:
        job_id: ID do job

    Returns:
        Status atual do job
    """
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job não encontrado")

    return jobs_db[job_id]


@app.get("/api/jobs")
async def list_jobs(limit: int = 50):
    """
    Lista todos os jobs

    Args:
        limit: Número máximo de jobs a retornar

    Returns:
        Lista de jobs
    """
    jobs = list(jobs_db.values())

    # Ordenar por data de criação (mais recente primeiro)
    jobs.sort(key=lambda x: x['started_at'], reverse=True)

    return {
        "total": len(jobs),
        "jobs": jobs[:limit]
    }


@app.post("/api/batch")
async def create_batch_animation(
    request: BatchRequest,
    background_tasks: BackgroundTasks
):
    """
    Cria animações em lote

    Returns:
        Lista de Job IDs
    """
    job_ids = []

    for image_path in request.image_paths:
        # Criar request individual
        anim_request = AnimationRequest(
            image_path=image_path,
            output_dir=request.output_dir,
            base_name=Path(image_path).stem,
            config_overrides=request.config_overrides
        )

        # Gerar ID e criar job
        job_id = str(uuid.uuid4())

        jobs_db[job_id] = {
            'job_id': job_id,
            'status': 'pending',
            'progress': 0,
            'message': 'Job criado (batch)',
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'results': None,
            'error': None
        }

        # Adicionar à fila
        background_tasks.add_task(process_animation, job_id, anim_request)
        job_ids.append(job_id)

    return {
        "batch_id": str(uuid.uuid4()),
        "job_ids": job_ids,
        "total": len(job_ids),
        "message": "Batch criado com sucesso"
    }


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload de imagem

    Returns:
        Caminho da imagem salva
    """
    try:
        # Criar diretório de uploads
        upload_dir = Path("assets/input")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Gerar nome único
        file_ext = Path(file.filename).suffix
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / file_name

        # Salvar arquivo
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        return {
            "filename": file_name,
            "path": str(file_path),
            "size": len(content)
        }

    except Exception as e:
        logger.error(f"Erro ao fazer upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{format}/{filename}")
async def download_video(format: str, filename: str):
    """
    Download de vídeo gerado

    Args:
        format: Formato (9x16 ou 16x9)
        filename: Nome do arquivo

    Returns:
        Arquivo de vídeo
    """
    output_dir = Path("assets/output")
    file_path = output_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=filename
    )


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Remove job do histórico

    Args:
        job_id: ID do job

    Returns:
        Confirmação
    """
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job não encontrado")

    del jobs_db[job_id]

    return {"message": "Job removido com sucesso"}


# Webhook endpoints para n8n
@app.post("/webhook/fiza-animate")
async def webhook_animate(
    request: AnimationRequest,
    background_tasks: BackgroundTasks
):
    """Webhook para n8n - criar animação"""
    return await create_animation(request, background_tasks)


@app.post("/webhook/fiza-batch")
async def webhook_batch(
    request: BatchRequest,
    background_tasks: BackgroundTasks
):
    """Webhook para n8n - processar em lote"""
    return await create_batch_animation(request, background_tasks)


@app.get("/webhook/fiza-status/{job_id}")
async def webhook_status(job_id: str):
    """Webhook para n8n - verificar status"""
    return await get_job_status(job_id)


def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False
):
    """Inicia servidor API"""
    logger.info(f"Iniciando servidor em {host}:{port}")

    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fiza Animator API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host")
    parser.add_argument("--port", type=int, default=8000, help="Porta")
    parser.add_argument("--reload", action="store_true", help="Auto-reload")

    args = parser.parse_args()

    start_server(args.host, args.port, args.reload)
