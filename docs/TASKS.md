# Quadro de Tarefas do Projeto (TASKS.md)

> **Status:** PROJETO 100% CONCLUÍDO E PRONTO PARA USO! 🚀  
> **Dono:** Engenheiro de MLOps & DevOps  
> **Data:** 17/11/2026

---

## [DBA] Banco de Dados & Modelagem
- [x] Configurar conexão SQLAlchemy 2.0 com suporte a SQLite (modo local padrão) e PostgreSQL
- [x] Implementar modelos ORM em `src/models/`: `User`, `Institution`, `Invoice`, `InvoiceItem`, `Category`, `CategorizationRule`
- [x] Configurar Alembic para versionamento de schema do banco
- [x] Criar migração inicial de tabelas (`migrations/versions/ef6d5a505771_initial_schema.py`)
- [x] Criar script de seed com instituições padrão (Nubank, Itaú, Bradesco, Caixa) e macrocategorias padrão (`src/core/seed.py`)

## [BACKEND] Lógica de Negócio & Serviços (src/)
- [x] Implementar classe abstrata `BaseInvoiceExtractor` e DTOs (`src/services/extractors/base.py`)
- [x] Implementar extrator especializado do **Nubank** com detecção de parcelas (`src/services/extractors/nubank.py`)
- [x] Implementar extrator especializado do **Itaú** (`src/services/extractors/itau.py`)
- [x] Implementar extrator especializado do **Bradesco** (`src/services/extractors/bradesco.py`)
- [x] Implementar extrator especializado da **Caixa Econômica** (`src/services/extractors/caixa.py`)
- [x] Implementar fábrica de extratores `ExtractorFactory` (`src/services/extractors/factory.py`)
- [x] Implementar motor de categorização automática e aprendizado por reforço (`src/services/categorizer.py`)
- [x] Implementar motor preditivo de parcelas futuras e compromissos orçamentários (`src/services/projections.py`)
- [x] Implementar serviço de métricas e agregação de histórico para BI (`src/services/analytics.py`)
- [x] Implementar serviço de autenticação e sessão local (`src/services/auth_service.py`)

## [FRONTEND] Interface Streamlit & BI Interativo
- [x] Criar folha de estilo customizada `assets/styles.css` (estilo Fintech Dark Mode, cards KPI, tipografia moderna)
- [x] Desenvolver ponto de entrada principal `app.py` com gerenciamento de sessão, autenticação e layout
- [x] Desenvolver página de upload de faturas (`pages/3_💳_Faturas_e_Upload.py`) com seletor de instituição e processamento
- [x] Desenvolver página de BI com KPIs consolidados e gráficos Plotly (`pages/1_📊_Dashboard_BI.py`)
- [x] Desenvolver página de Projeções Futuras (`pages/2_📈_Projecoes_Futuras.py`) com gráfico de fluxo de parcelas e tabela analítica
- [x] Desenvolver página de Categorias e Regras (`pages/4_🏷️_Categorias_e_Regras.py`) com reclassificação via `st.data_editor` para aprendizado por reforço
- [x] Implementar componentes reutilizáveis em `src/ui/` (`charts.py`, `metrics.py`, `tables.py`)

## [QA] Testes & Qualidade
- [x] Criar testes unitários para os extratores de PDF (com dados anonimizados representativos)
- [x] Criar testes unitários para a fórmula matemática e distribuição temporal de parcelas futuras (RN-03)
- [x] Criar testes unitários para o motor de aprendizado por reforço de categorização (RN-05)
- [x] Criar testes de integridade das entidades do banco e prevenção de duplicidade (RN-02)
- [x] Validar critérios de aceite das Histórias de Usuário US-01 a US-07 (`tests/test_qa_suite.py`)

## [MLOPS] Infraestrutura & Execução Local
- [x] Criar `requirements.txt` com todas as dependências fixadas
- [x] Criar `.env.example` com parâmetros de banco e segurança
- [x] Criar `Dockerfile` otimizado para a aplicação Streamlit
- [x] Criar `docker-compose.yml` para execução isolada com um único comando
- [x] Criar script de inicialização facilitada (`run.sh` e `Makefile`)
- [x] Criar pipeline de CI com GitHub Actions (`.github/workflows/ci.yml`)
- [x] Criar `.gitignore` para proteção de dados locais e banco SQLite

---

## Bugs Encontrados
- *Nenhum bug registrado.*
