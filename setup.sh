#!/bin/bash
# Script de setup automático para Fiza Cosmic Animator

set -e  # Exit on error

echo "🚀 Fiza Cosmic Animator - Setup"
echo "================================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funções auxiliares
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# 1. Verificar Python
echo "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 não encontrado. Por favor, instale Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
print_success "Python $PYTHON_VERSION encontrado"

# 2. Criar ambiente virtual
echo ""
echo "Criando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Ambiente virtual criado"
else
    print_info "Ambiente virtual já existe"
fi

# 3. Ativar ambiente virtual
echo ""
echo "Ativando ambiente virtual..."
source venv/bin/activate
print_success "Ambiente virtual ativado"

# 4. Atualizar pip
echo ""
echo "Atualizando pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "pip atualizado"

# 5. Instalar dependências
echo ""
echo "Instalando dependências..."
echo "(Isso pode demorar alguns minutos...)"
pip install -r requirements.txt > /dev/null 2>&1
print_success "Dependências instaladas"

# 6. Verificar CUDA
echo ""
echo "Verificando CUDA..."
if python -c "import torch; print(torch.cuda.is_available())" | grep -q "True"; then
    GPU_NAME=$(python -c "import torch; print(torch.cuda.get_device_name(0))" 2>/dev/null)
    print_success "CUDA disponível: $GPU_NAME"
else
    print_info "CUDA não disponível (vai usar CPU)"
fi

# 7. Criar diretórios
echo ""
echo "Criando estrutura de diretórios..."
mkdir -p assets/input assets/output assets/temp
touch assets/input/.gitkeep assets/output/.gitkeep assets/temp/.gitkeep
print_success "Diretórios criados"

# 8. Configurar .env
echo ""
if [ ! -f ".env" ]; then
    echo "Criando arquivo .env..."
    cp .env.example .env
    print_success "Arquivo .env criado"
    print_info "IMPORTANTE: Edite .env e adicione sua GEMINI_API_KEY"
else
    print_info "Arquivo .env já existe"
fi

# 9. Verificar FFmpeg
echo ""
echo "Verificando FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
    print_success "FFmpeg $FFMPEG_VERSION encontrado"

    # Verificar NVENC
    if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "h264_nvenc"; then
        print_success "NVENC disponível (GPU encoding)"
    else
        print_info "NVENC não disponível (vai usar CPU encoding)"
    fi
else
    print_info "FFmpeg não encontrado (instale para melhor performance)"
    echo "    Ubuntu/Debian: sudo apt install ffmpeg"
    echo "    Mac: brew install ffmpeg"
fi

# 10. Teste básico
echo ""
echo "Executando teste básico..."
if python -c "from scripts.main import FizaAnimator; print('OK')" 2>/dev/null | grep -q "OK"; then
    print_success "Imports funcionando corretamente"
else
    print_error "Erro ao importar módulos"
    print_info "Tente: pip install -r requirements.txt"
fi

# 11. Sumário
echo ""
echo "================================"
echo "Setup completo! 🎉"
echo "================================"
echo ""
echo "Próximos passos:"
echo ""
echo "1. Configure sua GEMINI_API_KEY no arquivo .env:"
echo "   nano .env"
echo ""
echo "2. Coloque uma imagem em assets/input/"
echo ""
echo "3. Execute sua primeira animação:"
echo "   python scripts/main.py assets/input/sua_imagem.png"
echo ""
echo "4. (Opcional) Inicie o servidor API:"
echo "   python scripts/api_server.py"
echo ""
echo "5. (Opcional) Configure workflows n8n:"
echo "   Veja: README.md seção 'Integração com n8n'"
echo ""
echo "Documentação completa: README.md"
echo "Guia rápido: docs/QUICKSTART.md"
echo ""
print_success "Boas animações! ✨🚀"
