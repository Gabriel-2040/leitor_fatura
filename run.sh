#!/usr/bin/env bash
set -e

# Garante que os executáveis do pip --user (~/.local/bin) estejam no PATH
export PATH="$HOME/.local/bin:$PATH"

echo "🚀 Iniciando Inteligência Financeira Pessoal..."

# 1. Garante que migrações e seed estejam atualizados
echo "📦 Verificando banco de dados e migrações..."
PYTHONPATH=. python3 -m alembic upgrade head 2>/dev/null || true
PYTHONPATH=. python3 src/core/seed.py 2>/dev/null || true

# 2. Inicia o Streamlit via módulo do Python (funciona mesmo sem o executável direto no PATH)
echo "✨ Subindo interface Streamlit na porta 8501..."
python3 -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
