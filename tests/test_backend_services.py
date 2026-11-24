"""Testes unitários e de integração para os serviços de backend e regras de negócio."""

from datetime import date
from src.core.database import SessionLocal
from src.services.auth_service import AuthService
from src.services.extractors.base import BaseInvoiceExtractor
from src.services.extractors.factory import ExtractorFactory
from src.services.categorizer import CategorizerService
from src.services.projections import ProjectionService
from src.models.institution import Institution
from src.models.category import Category
from src.models.invoice import Invoice
from src.models.invoice_item import InvoiceItem

def test_auth_service():
    db = SessionLocal()
    try:
        user = AuthService.get_or_create_default_user(db)
        assert user is not None
        assert user.email == "admin@local.com"

        auth = AuthService.authenticate_user(db, "admin@local.com", "admin")
        assert auth is not None
        assert auth.id == user.id

        wrong_auth = AuthService.authenticate_user(db, "admin@local.com", "wrong")
        assert wrong_auth is None
        print("✓ AuthService validado com sucesso")
    finally:
        db.close()

def test_extractors_helpers():
    # 1. Moeda
    assert BaseInvoiceExtractor.parse_currency("R$ 1.250,50") == 1250.50
    assert BaseInvoiceExtractor.parse_currency("45,00") == 45.00
    assert BaseInvoiceExtractor.parse_currency("-100,20") == -100.20
    assert BaseInvoiceExtractor.parse_currency("50,00 CR") == -50.00

    # 2. Parcelamento
    curr, tot, desc = BaseInvoiceExtractor.extract_installment("MAGAZINE LUIZA 02/10")
    assert curr == 2 and tot == 10 and desc == "MAGAZINE LUIZA"

    curr2, tot2, desc2 = BaseInvoiceExtractor.extract_installment("COMPRA PARCELA 1 DE 5")
    assert curr2 == 1 and tot2 == 5 and desc2 == "COMPRA"

    curr3, tot3, desc3 = BaseInvoiceExtractor.extract_installment("PADARIA SEM PARCELA")
    assert curr3 == 1 and tot3 == 1 and desc3 == "PADARIA SEM PARCELA"

    # 3. Factory
    for slug in ["nubank", "itau", "bradesco", "caixa"]:
        extractor = ExtractorFactory.get_extractor(slug)
        assert extractor is not None
    print("✓ Extratores e utilitários validados com sucesso")

def test_categorization_and_reinforcement():
    db = SessionLocal()
    try:
        user = AuthService.get_or_create_default_user(db)
        
        # 1. Teste de Dicionário Léxico
        cat_ifood = CategorizerService.categorize(db, user.id, "IFOOD *RESTAURANTE")
        assert cat_ifood.name == "Alimentação"

        cat_posto = CategorizerService.categorize(db, user.id, "POSTO SHELL COMBUSTIVEL")
        assert cat_posto.name == "Transporte / Combustível"

        cat_unknown = CategorizerService.categorize(db, user.id, "LOJA DESCONHECIDA XYZ 999")
        assert cat_unknown.name == "Outros"

        # 2. Teste de Aprendizado por Reforço (RN-05)
        # Cria uma fatura e item temporários para simular a intervenção manual do usuário
        inst = db.query(Institution).filter_by(slug="nubank").first()
        cat_saude = db.query(Category).filter_by(name="Saúde / Farmácia").first()

        inv = Invoice(
            user_id=user.id,
            institution_id=inst.id,
            reference_month=1,
            reference_year=2026,
            due_date=date(2026, 1, 20),
            total_amount=150.0,
        )
        db.add(inv)
        db.flush()

        item = InvoiceItem(
            invoice_id=inv.id,
            category_id=cat_unknown.id,
            purchase_date=date(2026, 1, 5),
            description="SUPLEMENTOS FITNESS POWER",
            amount=150.0,
        )
        db.add(item)
        db.commit()

        # O usuário reclassifica para "Saúde / Farmácia"
        CategorizerService.reclassify_item(
            db=db,
            user_id=user.id,
            item_id=item.id,
            new_category_id=cat_saude.id,
            apply_to_future=True,
        )

        # Agora, uma nova descrição contendo "SUPLEMENTOS FITNESS POWER" deve ser categorizada como "Saúde / Farmácia"!
        learned_cat = CategorizerService.categorize(db, user.id, "COMPRA SUPLEMENTOS FITNESS POWER")
        assert learned_cat.name == "Saúde / Farmácia", f"Esperado Saúde / Farmácia, obtido {learned_cat.name}"

        # Limpeza
        db.delete(item)
        db.delete(inv)
        db.commit()
        print("✓ Motor de categorização e aprendizado por reforço validado com sucesso")
    finally:
        db.close()

def test_projections_engine():
    db = SessionLocal()
    try:
        user = AuthService.get_or_create_default_user(db)
        inst = db.query(Institution).filter_by(slug="itau").first()
        cat = db.query(Category).first()

        # Simula fatura de Março/2026 com compra em 5 parcelas, estando na parcela 2 (restam 3 meses: Abr, Mai, Jun)
        inv = Invoice(
            user_id=user.id,
            institution_id=inst.id,
            reference_month=3,
            reference_year=2026,
            due_date=date(2026, 3, 10),
            total_amount=300.0,
        )
        db.add(inv)
        db.flush()

        item = InvoiceItem(
            invoice_id=inv.id,
            category_id=cat.id,
            purchase_date=date(2026, 2, 1),
            description="SMARTPHONE GALAXY",
            amount=100.0,
            current_installment=2,
            total_installments=5,
        )
        db.add(item)
        db.commit()

        # Executa cálculo de projeções (RN-03)
        proj_data = ProjectionService.calculate_future_projections(db, user.id, months_ahead=6)
        projections = proj_data["projections"]

        # Devem ser projetados os meses 2026-04, 2026-05, 2026-06 (3 parcelas restantes de R$ 100 cada = R$ 300)
        assert proj_data["total_committed"] >= 300.0, f"Total comprometido esperado >= 300, obtido {proj_data['total_committed']}"

        periods = [p["period"] for p in projections]
        assert "2026-04" in periods
        assert "2026-05" in periods
        assert "2026-06" in periods
        assert "2026-07" not in periods  # Parcela encerrada!

        # Limpeza
        db.delete(item)
        db.delete(inv)
        db.commit()
        print("✓ Motor de projeção de parcelas futuras (RN-03) validado com sucesso")
    finally:
        db.close()

if __name__ == "__main__":
    test_auth_service()
    test_extractors_helpers()
    test_categorization_and_reinforcement()
    test_projections_engine()
    print("\n🎉 TODOS OS TESTES DE BACKEND PASSARAM COM 100% DE SUCESSO!")
