.PHONY: help install run test migrate docker-build docker-up docker-down

help:
	@echo "Comandos disponíveis:"
	@echo "  make run          - Inicia a aplicação Streamlit localmente"
	@echo "  make test         - Executa todos os testes de QA e auditoria"
	@echo "  make migrate      - Executa migrações do banco com Alembic"
	@echo "  make seed         - Popula bancos e categorias padrão"
	@echo "  make docker-up    - Sobe a aplicação em container Docker via Compose"
	@echo "  make docker-down  - Para o container Docker"

run:
	@export PATH="$$HOME/.local/bin:$$PATH" && python3 -m streamlit run app.py --server.port 8501

test:
	@PYTHONPATH=. python3 tests/test_qa_suite.py -v
	@PYTHONPATH=. python3 tests/test_database.py
	@PYTHONPATH=. python3 tests/test_backend_services.py

migrate:
	@PYTHONPATH=. alembic upgrade head

seed:
	@PYTHONPATH=. python3 src/core/seed.py

docker-build:
	@docker compose build

docker-up:
	@docker compose up -d
	@echo "Aplicação disponível em: http://localhost:8501"

docker-down:
	@docker compose down
