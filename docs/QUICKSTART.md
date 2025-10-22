# Guia de Início Rápido 🚀

Este guia vai te ajudar a começar a usar o Fiza Cosmic Animator em 5 minutos!

## ⚡ Setup Rápido

### 1. Instalar Dependências (5 min)

```bash
# Clone o repositório
cd animacao_home

# Crie e ative ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate no Windows

# Instale dependências
pip install -r requirements.txt
```

### 2. Configurar API Key (1 min)

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite e adicione sua chave Gemini
echo "GEMINI_API_KEY=sua_chave_aqui" > .env
```

Obtenha sua chave em: https://makersuite.google.com/app/apikey

### 3. Teste Básico (1 min)

```bash
# Coloque uma imagem 1:1 em assets/input/
# Por exemplo: assets/input/fiza_test.png

# Execute o animador
python scripts/main.py assets/input/fiza_test.png
```

Aguarde 3-5 minutos e os vídeos estarão em `assets/output/`!

## 📱 Primeiro Uso

### Preparar sua Imagem

Para melhores resultados:

1. **Formato**: PNG ou JPG
2. **Aspect Ratio**: 1:1 (quadrada) de preferência
3. **Resolução**: Pelo menos 2048x2048 para melhor qualidade
4. **Conteúdo**: Personagem centralizado, fundo cósmico/espacial

### Executar Animação

```bash
python scripts/main.py assets/input/sua_imagem.png
```

O sistema irá:
1. Gerar keyframes com Gemini (30-60s)
2. Interpolar frames intermediários (1-2 min)
3. Aplicar efeitos cósmicos (30s)
4. Renderizar 2 vídeos: 9:16 e 16:9 (30s)

**Total**: ~3-5 minutos

### Resultado

Você receberá:
- `sua_imagem_9x16.mp4` - Vídeo vertical (shorts)
- `sua_imagem_16x9.mp4` - Vídeo horizontal
- `sua_imagem_preview.gif` - Preview animado
- Pasta `keyframes/` - Frames-chave gerados
- Pasta `samples/` - Amostras dos frames processados

## 🎨 Customização Rápida

### Mais Partículas

```bash
# Edite config/config.yaml
animation:
  effects:
    particles:
      count: 500  # Padrão: 200
```

### Vídeo Mais Longo

```bash
animation:
  duration: 10  # 10 segundos
  fps: 30
```

### Glow Mais Intenso

```bash
animation:
  effects:
    glow:
      intensity: 1.2  # Padrão: 0.8
      radius: 20      # Padrão: 15
```

## 🚀 Próximos Passos

1. **Explorar efeitos**: Veja `config/config.yaml` para todas as opções
2. **API Server**: `python scripts/api_server.py` para modo servidor
3. **n8n**: Configure workflows automáticos (veja README)
4. **Batch**: Processe múltiplas imagens de uma vez

## ❓ Problemas Comuns

### "CUDA not available"

Não é problema! O sistema funciona em CPU também, só será um pouco mais lento.

Para habilitar CUDA:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### "Gemini API Error"

Verifique:
1. Chave está correta no `.env`
2. Tem internet
3. Tem créditos na conta Gemini

### Vídeo muito rápido/lento

Ajuste FPS ou duração no `config/config.yaml`:
```yaml
animation:
  fps: 24        # Menos frames = mais rápido
  duration: 8    # Mais segundos = mais longo
```

## 💡 Dicas

1. **Primeira vez**: Use imagem pequena (512x512) para testar rápido
2. **Produção**: Use imagem grande (2048x2048+) para qualidade máxima
3. **Experimente**: Mude valores no config.yaml e veja o resultado!
4. **Batch**: Processe várias imagens à noite enquanto dorme

## 📊 O Que Esperar

### Qualidade

- **Excelente**: Efeitos de partículas, glow, movimento
- **Boa**: Interpolação suave entre frames
- **Variável**: Qualidade do Gemini (depende do prompt/imagem)

### Performance (RTX 4070)

- Animação 5s @ 30fps: ~3-5 minutos
- Com CPU only: ~10-15 minutos

### Custos

- **Gemini API**: ~10-20 keyframes por animação
- **GPU**: Grátis (local)
- **n8n**: Grátis (self-hosted)

## 🎬 Exemplo Completo

```bash
# 1. Preparar
cd animacao_home
source venv/bin/activate

# 2. Configurar
export GEMINI_API_KEY="sua_chave"

# 3. Animar
python scripts/main.py assets/input/fiza.png \
  --output assets/output/teste \
  --name fiza_cosmic_v1

# 4. Resultado em:
# assets/output/teste/fiza_cosmic_v1_9x16.mp4
# assets/output/teste/fiza_cosmic_v1_16x9.mp4
```

## 🆘 Precisa de Ajuda?

- Documentação completa: `README.md`
- Issues: GitHub Issues
- Email: seu-email@exemplo.com

Boa animação! ✨🚀
