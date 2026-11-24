import re
from typing import Optional, Dict
from sqlalchemy.orm import Session
from src.models.category import Category
from src.models.categorization_rule import CategorizationRule
from src.models.invoice_item import InvoiceItem

# Dicionário Léxico Padrão de Mercado
DEFAULT_LEXICON: Dict[str, list[str]] = {
    "Alimentação": [
        "IFOOD", "RESTAURANTE", "BURGER", "MCDONALDS", "SUBWAY", "HABIB", "PIZZARIA", "LANCHES",
        "BAR", "PADARIA", "CAFETERIA", "STARBUCKS", "OUTBACK", "CHURRASCARIA", "DOCERIA", "SORVETE"
    ],
    "Supermercado": [
        "MERCADO", "SUPERMERCADO", "CARREFOUR", "PAO DE ACUCAR", "ASSAI", "ATACADAO", "EXTRA",
        "BIG", "DIA", "HORTIFRUTI", "SACOLÃO", "QUITANDA", "ZE DELIVERY", "MAMBO"
    ],
    "Transporte / Combustível": [
        "UBER", "99APP", "99 TECNOLOGIA", "POSTO", "IPIRANGA", "SHELL", "PETROBRAS", "BR MANIA",
        "AUTO POSTO", "SEM PARAR", "VELOE", "CONECTCAR", "ESTAPAR", "PEDAGIO", "TAXI", "COMBUSTIVEL"
    ],
    "Saúde / Farmácia": [
        "DROGASIL", "DROGARIA", "FARMACIA", "RAIA", "DROGA RAIA", "PAGUE MENOS", "SAO PAULO",
        "LABORATORIO", "CONSULTA", "MEDICO", "HOSPITAL", "CLINICA", "DENTISTA", "ODONTO", "EXAME"
    ],
    "Moradia / Serviços": [
        "ENEL", "CPFL", "LIGHT", "SABESP", "COPASA", "SANEPAR", "COMGAS", "CONDOMINIO", "ALUGUEL",
        "INTERNET", "CLARO", "VIVO", "TIM", "OI", "TELECOM", "ENERGIA", "AGUA", "GAS"
    ],
    "Lazer / Entretenimento": [
        "CINEMA", "CINEMARK", "CINEPOLIS", "INGRESSO", "SHOW", "TEATRO", "HOTEL", "POUSADA",
        "AIRBNB", "BOOKING", "VIAGEM", "RESORT", "PARQUE", "STEAM", "PLAYSTATION", "XBOX"
    ],
    "Educação": [
        "FACULDADE", "UNIVERSIDADE", "ESCOLA", "CURSO", "UDEMY", "ALURA", "COURSERA", "LIVRARIA",
        "SARAIVA", "CULTURA", "IDIOMAS", "INGLES", "LIVRO"
    ],
    "Compras / Vestuário": [
        "AMAZON", "MERCADO LIVRE", "MAGAZINE LUIZA", "MAGALU", "SHOPEE", "ALIEXPRESS", "SHEIN",
        "ZARA", "RENNER", "RIACHUELO", "C&A", "CENTAURO", "NETSHOES", "NIKE", "ADIDAS", "DECATHLON"
    ],
    "Assinaturas / Streaming": [
        "NETFLIX", "SPOTIFY", "AMAZON PRIME", "DISNEY", "HBO", "MAX", "YOUTUBE", "APPLE.COM/BILL",
        "GOOGLE STORAGE", "CHATGPT", "OPENAI", "DEEZER", "GLOBOPLAY", "CRUNCHYROLL"
    ],
    "Tarifas / Juros": [
        "ANUIDADE", "TARIFA", "JUROS", "MULTA", "IOF", "ENCARGOS", "MORA"
    ],
}

class CategorizerService:
    @classmethod
    def get_category_by_name(cls, db: Session, name: str) -> Optional[Category]:
        return db.query(Category).filter(Category.name.ilike(name.strip())).first()

    @classmethod
    def get_default_category(cls, db: Session) -> Category:
        """Retorna a categoria residual 'Outros'."""
        cat = db.query(Category).filter(Category.name == "Outros").first()
        if not cat:
            cat = Category(name="Outros", color_hex="#94A3B8", icon_name="tag", is_default=True)
            db.add(cat)
            db.commit()
            db.refresh(cat)
        return cat

    @classmethod
    def categorize(cls, db: Session, user_id: str, description: str) -> Category:
        """
        Categoriza a descrição de um lançamento:
        1. Regras personalizadas aprendidas do usuário (prioridade máxima).
        2. Dicionário léxico padrão.
        3. Categoria residual 'Outros'.
        """
        desc_clean = description.strip().upper()

        # 1. Regras personalizadas do usuário
        user_rules = (
            db.query(CategorizationRule)
            .filter(CategorizationRule.user_id == user_id)
            .order_by(CategorizationRule.priority.desc())
            .all()
        )
        for rule in user_rules:
            pattern = rule.pattern.strip().upper()
            if rule.match_type == "EXACT" and desc_clean == pattern:
                return rule.category
            elif rule.match_type == "CONTAINS" and pattern in desc_clean:
                return rule.category
            elif rule.match_type == "REGEX":
                if re.search(pattern, desc_clean):
                    return rule.category

        # 2. Dicionário Léxico Padrão
        for category_name, keywords in DEFAULT_LEXICON.items():
            for kw in keywords:
                if kw in desc_clean:
                    cat = cls.get_category_by_name(db, category_name)
                    if cat:
                        return cat

        # 3. Residual 'Outros'
        return cls.get_default_category(db)

    @classmethod
    def reclassify_item(
        cls,
        db: Session,
        user_id: str,
        item_id: str,
        new_category_id: str,
        apply_to_future: bool = True
    ) -> InvoiceItem:
        """
        Reclassifica um item e, se solicitado, grava a regra para memorização contínua (reforço).
        """
        item = db.query(InvoiceItem).filter(InvoiceItem.id == item_id).first()
        if not item:
            raise ValueError(f"Item com ID '{item_id}' não encontrado.")

        new_category = db.query(Category).filter(Category.id == new_category_id).first()
        if not new_category:
            raise ValueError(f"Categoria com ID '{new_category_id}' não encontrada.")

        item.category_id = new_category.id

        if apply_to_future:
            # Limpa o texto da descrição para usar como padrão chave (remove números residuais e pontuações)
            clean_pattern = re.sub(r'[\d\.\-\*/]+', ' ', item.description).strip()
            if not clean_pattern:
                clean_pattern = item.description.strip()

            clean_pattern = clean_pattern.upper()

            # Verifica se já existe uma regra igual para atualizar ou cria nova
            existing_rule = (
                db.query(CategorizationRule)
                .filter(
                    CategorizationRule.user_id == user_id,
                    CategorizationRule.pattern == clean_pattern
                )
                .first()
            )

            if existing_rule:
                existing_rule.category_id = new_category.id
            else:
                rule = CategorizationRule(
                    user_id=user_id,
                    category_id=new_category.id,
                    pattern=clean_pattern,
                    match_type="CONTAINS",
                    priority=10,  # Prioridade alta para regra de reforço
                )
                db.add(rule)

        db.commit()
        db.refresh(item)
        return item
