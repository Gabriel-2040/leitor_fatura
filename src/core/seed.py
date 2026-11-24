"""Script de carga inicial (seed) para instituições e categorias padrão."""

from src.core.database import SessionLocal
from src.models.institution import Institution
from src.models.category import Category

DEFAULT_INSTITUTIONS = [
    {"name": "Nubank", "slug": "nubank", "color_hex": "#8A05BE"},
    {"name": "Itaú", "slug": "itau", "color_hex": "#EC7000"},
    {"name": "Bradesco", "slug": "bradesco", "color_hex": "#CC092F"},
    {"name": "Caixa Econômica Federal", "slug": "caixa", "color_hex": "#005CA9"},
]

DEFAULT_CATEGORIES = [
    {"name": "Alimentação", "color_hex": "#10B981", "icon_name": "utensils"},
    {"name": "Supermercado", "color_hex": "#059669", "icon_name": "shopping-cart"},
    {"name": "Transporte / Combustível", "color_hex": "#F59E0B", "icon_name": "car"},
    {"name": "Saúde / Farmácia", "color_hex": "#EF4444", "icon_name": "heart-pulse"},
    {"name": "Moradia / Serviços", "color_hex": "#3B82F6", "icon_name": "home"},
    {"name": "Lazer / Entretenimento", "color_hex": "#8B5CF6", "icon_name": "film"},
    {"name": "Educação", "color_hex": "#6366F1", "icon_name": "graduation-cap"},
    {"name": "Compras / Vestuário", "color_hex": "#EC4899", "icon_name": "shopping-bag"},
    {"name": "Assinaturas / Streaming", "color_hex": "#06B6D4", "icon_name": "repeat"},
    {"name": "Tarifas / Juros", "color_hex": "#64748B", "icon_name": "alert-circle"},
    {"name": "Outros", "color_hex": "#94A3B8", "icon_name": "tag"},
]

def seed_database():
    """Popula o banco com os dados essenciais caso ainda não existam."""
    db = SessionLocal()
    try:
        # 1. Popula Instituições
        for inst_data in DEFAULT_INSTITUTIONS:
            exists = db.query(Institution).filter_by(slug=inst_data["slug"]).first()
            if not exists:
                inst = Institution(
                    name=inst_data["name"],
                    slug=inst_data["slug"],
                    color_hex=inst_data["color_hex"]
                )
                db.add(inst)

        # 2. Popula Categorias
        for cat_data in DEFAULT_CATEGORIES:
            exists = db.query(Category).filter_by(name=cat_data["name"]).first()
            if not exists:
                cat = Category(
                    name=cat_data["name"],
                    color_hex=cat_data["color_hex"],
                    icon_name=cat_data["icon_name"],
                    is_default=True
                )
                db.add(cat)

        db.commit()
        print("Seed executado com sucesso: Instituições e Categorias padrão configuradas.")
    except Exception as e:
        db.rollback()
        print(f"Erro ao executar seed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
