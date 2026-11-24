"""Testes automatizados para a camada de persistência e modelos ORM."""

from src.core.database import SessionLocal
from src.models.institution import Institution
from src.models.category import Category
from src.models.user import User

def test_initial_seed_loaded():
    db = SessionLocal()
    try:
        institutions = db.query(Institution).all()
        assert len(institutions) == 4, f"Esperado 4 instituições, encontrado {len(institutions)}"
        
        slugs = {inst.slug for inst in institutions}
        assert {"nubank", "itau", "bradesco", "caixa"}.issubset(slugs)

        categories = db.query(Category).all()
        assert len(categories) >= 10, f"Esperado pelo menos 10 categorias, encontrado {len(categories)}"
    finally:
        db.close()

if __name__ == "__main__":
    test_initial_seed_loaded()
    print("Todos os testes de banco de dados passaram com sucesso!")
