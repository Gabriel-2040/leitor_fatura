## Teste em andamento usando o antigravity como parceiro para desenvolvimento de bi com uso de css para melhor visualização dos estilos do streamlit.
# 💳 Inteligência Financeira Pessoal (Leitor de Faturas & BI)

> Aplicativo de inteligência financeira pessoal que transforma faturas de cartão de crédito em um painel BI analítico com **projeções preditivas de gastos futuros** (baseadas em parcelamentos ativos) e **categorização contínua com aprendizado por reforço**.

---

## 🚀 Principais Funcionalidades

1. **Extratores Especializados por Emissor:**
   - Suporte nativo para faturas em PDF de **Nubank**, **Itaú**, **Bradesco** e **Caixa Econômica Federal**.
   - Identificação automática de metadados da fatura (vencimento, melhor dia/fechamento, total) e de cada lançamento.
   - Detecção precisa de parcelamentos (ex: `01/06`, `02/10`, `Parcela 3 de 5`).

2. **Categorização Inteligente com Aprendizado por Reforço (RN-05):**
   - Classificação léxica automática em 10 macrocategorias (*Alimentação, Supermercado, Transporte, Saúde, Moradia, Lazer, Educação, Compras, Assinaturas, Tarifas*).
   - Reclassificação instantânea pelo usuário via tabela interativa (`st.data_editor`).
   - O sistema memoriza suas correções em `categorization_rules` e prioriza seu histórico nas próximas faturas.

3. **Painel BI Interativo (Plotly):**
   - Gráfico de Rosca (*Donut Chart*) com distribuição percentual por macrocategoria.
   - Gráfico de Barras com evolução histórica mês a mês das faturas.
   - Cards de KPI: Total atual, comparativo percentual vs mês anterior e categoria de maior impacto.

4. **Motor Preditivo de Gastos Futuros (RN-03):**
   - Cálculo exato das parcelas restantes ($N - P$) para cada compra ativa.
   - Distribuição temporal automática dos compromissos nos meses subsequentes ($M+1, M+2, \dots, M+R$).
   - Gráfico de Curva de Quitação e drill-down em abas detalhadas mês a mês.

5. **Privacidade e Armazenamento 100% Local (RN-01):**
   - Todos os dados financeiros e arquivos PDF permanecem estritamente no seu computador local (banco SQLite com modo WAL).

---

## 🛠️ Stack Tecnológica

- **Linguagem & Backend:** Python 3.12+ (SQLAlchemy 2.0, Alembic, Pydantic v2, Passlib/Bcrypt)
- **Extração de PDF:** `pdfplumber` e `pypdf`
- **Frontend & BI:** Streamlit + CSS Customizado (*Fintech Dark Mode*) + Plotly Interativo
- **Infraestrutura:** Docker, Docker Compose e GitHub Actions CI

---

## ⚡ Como Executar

### Opção 1: Execução Local Direta (Recomendado)

```bash
# 1. Instale as dependências (se ainda não instalou)
pip install -r requirements.txt

# 2. Inicialize as migrações e o banco de dados
alembic upgrade head
python src/core/seed.py

# 3. Inicie o aplicativo Streamlit
./run.sh
# ou
python3 -m streamlit run app.py
```
Acesse no seu navegador: **`http://localhost:8501`**

---

### Opção 2: Execução via Docker Compose

```bash
# Sobe o container isolado da aplicação
docker compose up -d

# Para verificar os logs
docker compose logs -f

# Para parar
docker compose down
```

---

## 🧪 Executando os Testes Automatizados

O projeto possui suíte completa de testes de QA cobrindo todos os critérios de aceite do PRD:

```bash
# Executa todos os testes
make test
# ou manualmente:
python3 tests/test_qa_suite.py -v
python3 tests/test_database.py
python3 tests/test_backend_services.py
```

---

## 📂 Estrutura do Repositório

```text
├── assets/
│   └── styles.css              # Tema executivo Fintech Dark Mode
├── docs/                       # Documentação oficial
│   ├── PRD.md                  # Requisitos e critérios de aceite
│   ├── ARCHITECTURE.md         # Decisões de arquitetura e diagramas
│   └── TASKS.md                # Quadro de tarefas e progresso
├── migrations/                 # Migrações versionadas do Alembic
├── pages/                      # Telas da aplicação Streamlit
│   ├── 1_📊_Dashboard_BI.py
│   ├── 2_📈_Projecoes_Futuras.py
│   ├── 3_💳_Faturas_e_Upload.py
│   └── 4_🏷️_Categorias_e_Regras.py
├── src/                        # Núcleo de domínio desacoplado
│   ├── core/                   # Banco de dados e configurações
│   ├── models/                 # Modelos ORM (User, Invoice, Item, etc.)
│   ├── services/               # Extratores, Categorizador e Projeções
│   │   └── extractors/         # Nubank, Itaú, Bradesco e Caixa
│   └── ui/                     # Componentes visuais (Gráficos, KPIs, Tabelas)
├── tests/                      # Suíte de testes automatizados e QA
├── app.py                      # Ponto de entrada Streamlit
├── docker-compose.yml          # Orquestração Docker
├── Dockerfile                  # Container multi-stage
├── Makefile                    # Comandos rápidos de automação
├── requirements.txt            # Dependências Python
└── run.sh                      # Script facilitador de execução
```
