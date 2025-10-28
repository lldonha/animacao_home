"""
Script para download de modelos recomendados
"""

import os
import argparse
from pathlib import Path
from huggingface_hub import snapshot_download, hf_hub_download
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Modelos recomendados
RECOMMENDED_MODELS = {
    "stable_diffusion": [
        {
            "name": "Realistic Vision V5.1",
            "repo_id": "SG161222/Realistic_Vision_V5.1_noVAE",
            "description": "Modelo realista excelente para personagens",
            "size": "~5GB"
        },
        {
            "name": "DreamShaper XL",
            "repo_id": "Lykon/dreamshaper-xl-1-0",
            "description": "SDXL - Alta qualidade e versatilidade",
            "size": "~7GB"
        },
        {
            "name": "Realistic Vision V6 (B1)",
            "repo_id": "stablediffusionapi/realistic-vision-v6",
            "description": "Versão mais recente do Realistic Vision",
            "size": "~5GB"
        }
    ],
    "controlnet": [
        {
            "name": "ControlNet Canny",
            "repo_id": "lllyasviel/control_v11p_sd15_canny",
            "description": "ControlNet para detecção de bordas",
            "size": "~1.5GB"
        },
        {
            "name": "ControlNet Tile",
            "repo_id": "lllyasviel/control_v11f1e_sd15_tile",
            "description": "Para upscaling e refinamento",
            "size": "~1.5GB"
        }
    ],
    "animation": [
        {
            "name": "AnimateDiff Motion Module",
            "repo_id": "guoyww/animatediff-motion-adapter-v1-5-2",
            "description": "Módulo de movimento AnimateDiff",
            "size": "~1.8GB"
        }
    ],
    "upscaling": [
        {
            "name": "Real-ESRGAN",
            "repo_id": "ai-forever/Real-ESRGAN",
            "description": "Upscaling de alta qualidade",
            "size": "~200MB"
        }
    ]
}


def download_model(
    repo_id: str,
    local_dir: Path,
    model_type: str = "stable_diffusion"
):
    """
    Download de modelo do Hugging Face

    Args:
        repo_id: ID do repositório no HF
        local_dir: Diretório local
        model_type: Tipo de modelo
    """
    logger.info(f"Baixando {repo_id}...")

    target_dir = local_dir / model_type / repo_id.split('/')[-1]
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Download completo do modelo
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(target_dir),
            local_dir_use_symlinks=False,
            resume_download=True
        )

        logger.info(f"✓ Download completo: {repo_id}")
        logger.info(f"  Localização: {target_dir}")

        return True

    except Exception as e:
        logger.error(f"✗ Erro ao baixar {repo_id}: {e}")
        return False


def download_category(
    category: str,
    models_dir: Path,
    model_indices: list = None
):
    """
    Download de uma categoria de modelos

    Args:
        category: Categoria (stable_diffusion, controlnet, etc)
        models_dir: Diretório de modelos
        model_indices: Índices específicos para baixar (None = todos)
    """
    if category not in RECOMMENDED_MODELS:
        logger.error(f"Categoria desconhecida: {category}")
        return

    models = RECOMMENDED_MODELS[category]

    if model_indices:
        models = [models[i] for i in model_indices if i < len(models)]

    logger.info(f"\n{'='*60}")
    logger.info(f"Categoria: {category.upper()}")
    logger.info(f"{'='*60}\n")

    for model in models:
        logger.info(f"\nModelo: {model['name']}")
        logger.info(f"Descrição: {model['description']}")
        logger.info(f"Tamanho: {model['size']}")

        download_model(
            repo_id=model['repo_id'],
            local_dir=models_dir,
            model_type=category
        )


def list_models():
    """Lista todos os modelos recomendados"""
    print("\n" + "="*60)
    print("MODELOS RECOMENDADOS PARA FIZA COSMIC ANIMATOR")
    print("="*60 + "\n")

    for category, models in RECOMMENDED_MODELS.items():
        print(f"\n{category.upper().replace('_', ' ')}")
        print("-" * 60)

        for i, model in enumerate(models):
            print(f"\n[{i}] {model['name']}")
            print(f"    Repo: {model['repo_id']}")
            print(f"    {model['description']}")
            print(f"    Tamanho: {model['size']}")

    print("\n" + "="*60 + "\n")


def download_minimal_setup(models_dir: Path):
    """Download do setup mínimo recomendado"""
    logger.info("\n" + "="*60)
    logger.info("SETUP MÍNIMO RECOMENDADO")
    logger.info("="*60 + "\n")

    logger.info("Este setup inclui:")
    logger.info("  - 1 modelo Stable Diffusion (Realistic Vision)")
    logger.info("  - 1 ControlNet (Canny)")
    logger.info("  - AnimateDiff Motion Module")
    logger.info("\nTamanho total: ~8GB\n")

    # Realistic Vision
    download_model(
        "SG161222/Realistic_Vision_V5.1_noVAE",
        models_dir,
        "stable_diffusion"
    )

    # ControlNet Canny
    download_model(
        "lllyasviel/control_v11p_sd15_canny",
        models_dir,
        "controlnet"
    )

    # AnimateDiff
    download_model(
        "guoyww/animatediff-motion-adapter-v1-5-2",
        models_dir,
        "animation"
    )

    logger.info("\n✓ Setup mínimo completo!")


def download_full_setup(models_dir: Path):
    """Download do setup completo"""
    logger.info("\n" + "="*60)
    logger.info("SETUP COMPLETO")
    logger.info("="*60 + "\n")

    logger.info("Baixando todos os modelos recomendados...")
    logger.info("Tamanho total: ~25GB\n")

    for category in RECOMMENDED_MODELS.keys():
        download_category(category, models_dir)

    logger.info("\n✓ Setup completo!")


def main():
    parser = argparse.ArgumentParser(
        description="Download de modelos para Fiza Cosmic Animator"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar modelos disponíveis"
    )

    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Download do setup mínimo (~8GB)"
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Download do setup completo (~25GB)"
    )

    parser.add_argument(
        "--category",
        type=str,
        choices=list(RECOMMENDED_MODELS.keys()),
        help="Baixar categoria específica"
    )

    parser.add_argument(
        "--model",
        type=str,
        help="Baixar modelo específico (repo_id)"
    )

    parser.add_argument(
        "--models-dir",
        type=str,
        default="models",
        help="Diretório para salvar modelos"
    )

    args = parser.parse_args()

    models_dir = Path(args.models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    if args.list:
        list_models()

    elif args.minimal:
        download_minimal_setup(models_dir)

    elif args.full:
        download_full_setup(models_dir)

    elif args.category:
        download_category(args.category, models_dir)

    elif args.model:
        # Detectar categoria pelo repo_id
        category = "stable_diffusion"  # default

        for cat, models in RECOMMENDED_MODELS.items():
            if any(m['repo_id'] == args.model for m in models):
                category = cat
                break

        download_model(args.model, models_dir, category)

    else:
        parser.print_help()
        print("\nExemplos de uso:")
        print("  python download_models.py --list")
        print("  python download_models.py --minimal")
        print("  python download_models.py --category stable_diffusion")
        print("  python download_models.py --model SG161222/Realistic_Vision_V5.1_noVAE")


if __name__ == "__main__":
    main()
