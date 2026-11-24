# ==============================================================================
# Multi-stage Dockerfile para o Aplicativo de Inteligência Financeira (Streamlit)
# ==============================================================================

# Estágio 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Instala ferramentas essenciais de compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

# Estágio 2: Runner final
FROM python:3.12-slim AS runner

WORKDIR /app

# Instala dependências de runtime mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cria usuário não-root para execução segura
RUN useradd -m -u 1000 appuser

# Copia pacotes instalados do estágio builder
COPY --from=builder /root/.local /home/appuser/.local

# Ajusta PATH do usuário appuser
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copia o código da aplicação
COPY --chown=appuser:appuser . .

USER appuser

# Expõe a porta padrão do Streamlit
EXPOSE 8501

# Healthcheck nativo
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
