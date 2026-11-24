"""Suíte Oficial de Testes de QA & Auditoria de Conformidade com o PRD."""

import unittest
from datetime import date
from src.core.database import SessionLocal
from src.services.auth_service import AuthService
from src.services.extractors.base import BaseInvoiceExtractor
from src.services.extractors.factory import ExtractorFactory
from src.services.extractors.nubank import NubankExtractor
from src.services.extractors.itau import ItauExtractor
from src.services.extractors.bradesco import BradescoExtractor
from src.services.extractors.caixa import CaixaExtractor
from src.services.categorizer import CategorizerService
from src.services.projections import ProjectionService
from src.services.invoice_service import InvoiceService
from src.services.analytics import AnalyticsService
from src.models.institution import Institution
from src.models.category import Category
from src.models.invoice import Invoice
from src.models.invoice_item import InvoiceItem
from src.models.user import User

class TestQAAuditoria(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.user = AuthService.get_or_create_default_user(cls.db)
        
        # Cria um segundo usuário para auditoria de isolamento multiusuário (US-01)
        cls.user_b = AuthService.get_user_by_email(cls.db, "user_b@audit.com")
        if not cls.user_b:
            cls.user_b = AuthService.register_user(
                db=cls.db,
                name="Usuário B Audit",
                email="user_b@audit.com",
                password="password123"
            )

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    # -------------------------------------------------------------
    # 1. AUDITORIA US-01: Autenticação e Isolamento de Usuário
    # -------------------------------------------------------------
    def test_us01_user_authentication_and_isolation(self):
        """Audita se a autenticação é segura e se os dados entre usuários são 100% isolados."""
        # Validação de credenciais
        valid_auth = AuthService.authenticate_user(self.db, "user_b@audit.com", "password123")
        self.assertIsNotNone(valid_auth)
        self.assertEqual(valid_auth.email, "user_b@audit.com")

        invalid_auth = AuthService.authenticate_user(self.db, "user_b@audit.com", "senha_errada")
        self.assertIsNone(invalid_auth)

        # Prevenção de e-mail duplicado
        with self.assertRaises(ValueError):
            AuthService.register_user(self.db, "Outro", "user_b@audit.com", "123")

        # Isolamento de faturas entre usuários
        inst = self.db.query(Institution).filter_by(slug="nubank").first()
        inv_a = Invoice(
            user_id=self.user.id,
            institution_id=inst.id,
            reference_month=7,
            reference_year=2026,
            due_date=date(2026, 7, 25),
            total_amount=500.0,
        )
        self.db.add(inv_a)
        self.db.commit()

        # O Usuário B não deve enxergar a fatura do Usuário A
        invoices_b = InvoiceService.list_invoices(self.db, user_id=self.user_b.id)
        b_ids = [inv.id for inv in invoices_b]
        self.assertNotIn(inv_a.id, b_ids, "FALHA DE ISOLAMENTO: Usuário B enxergou fatura do Usuário A!")

        # Limpeza
        self.db.delete(inv_a)
        self.db.commit()

    # -------------------------------------------------------------
    # 2. AUDITORIA US-02 & US-03: Extração de Layouts Especializados
    # -------------------------------------------------------------
    def test_us02_extractor_factory_and_validation(self):
        """Audita a fábrica de extratores e rejeição de bancos não suportados."""
        for slug in ["nubank", "itau", "bradesco", "caixa"]:
            extractor = ExtractorFactory.get_extractor(slug)
            self.assertIsInstance(extractor, BaseInvoiceExtractor)

        with self.assertRaises(ValueError):
            ExtractorFactory.get_extractor("banco_inexistente")

    def test_us03_nubank_line_parsing(self):
        """Audita o extrator do Nubank em casos típicos e com parcelas."""
        ext = NubankExtractor()
        
        # Compra à vista com formato data DD MMM
        item1 = ext._parse_line("15 JAN Supermercado Pão de Açúcar 150,45", default_year=2026)
        self.assertIsNotNone(item1)
        self.assertEqual(item1.description, "Supermercado Pão de Açúcar")
        self.assertEqual(item1.amount, 150.45)
        self.assertEqual(item1.current_installment, 1)
        self.assertEqual(item1.total_installments, 1)

        # Compra parcelada
        item2 = ext._parse_line("18 FEV Magazine Luiza 03/10 89,90", default_year=2026)
        self.assertIsNotNone(item2)
        self.assertEqual(item2.description, "Magazine Luiza")
        self.assertEqual(item2.amount, 89.90)
        self.assertEqual(item2.current_installment, 3)
        self.assertEqual(item2.total_installments, 10)

        # Linha irrelevante de cabeçalho
        self.assertIsNone(ext._parse_line("TOTAL A PAGAR R$ 1.500,00", default_year=2026))

    def test_us03_itau_and_bradesco_parsing(self):
        """Audita extratores do Itaú e Bradesco com datas DD/MM e estornos."""
        itau_ext = ItauExtractor()
        item_itau = itau_ext._parse_line("10/04 DROGASIL FARMACIA 45,90", default_year=2026)
        self.assertIsNotNone(item_itau)
        self.assertEqual(item_itau.description, "DROGASIL FARMACIA")
        self.assertEqual(item_itau.amount, 45.90)

        brad_ext = BradescoExtractor()
        # Item com indicador C de crédito/estorno (RN-04)
        item_brad_cred = brad_ext._parse_line("05/04 ESTORNO COMPRA CANCELADA 50,00 C", default_year=2026)
        self.assertIsNotNone(item_brad_cred)
        self.assertEqual(item_brad_cred.amount, -50.00, "RN-04: Crédito/Estorno deve ser registrado com valor negativo")

    # -------------------------------------------------------------
    # 3. AUDITORIA US-04 & US-05: Categorização e Aprendizado por Reforço (RN-05)
    # -------------------------------------------------------------
    def test_us04_us05_categorization_and_reinforcement_learning(self):
        """Audita categorização automática e prevalência de regras aprendidas do usuário."""
        # 1. Dicionário Léxico Padrão
        cat_uber = CategorizerService.categorize(self.db, self.user.id, "UBER TRIP BRASIL")
        self.assertEqual(cat_uber.name, "Transporte / Combustível")

        cat_drogasil = CategorizerService.categorize(self.db, self.user.id, "DROGASIL VILA MARIANA")
        self.assertEqual(cat_drogasil.name, "Saúde / Farmácia")

        cat_netflix = CategorizerService.categorize(self.db, self.user.id, "NETFLIX.COM MENSALIDADE")
        self.assertEqual(cat_netflix.name, "Assinaturas / Streaming")

        # 2. Residual para termo desconhecido
        cat_desconhecido = CategorizerService.categorize(self.db, self.user.id, "ESTABELECIMENTO INEXISTENTE 999")
        self.assertEqual(cat_desconhecido.name, "Outros")

        # 3. Intervenção do Usuário e Aprendizado por Reforço (RN-05)
        inst = self.db.query(Institution).filter_by(slug="itau").first()
        cat_lazer = self.db.query(Category).filter_by(name="Lazer / Entretenimento").first()

        inv = Invoice(
            user_id=self.user.id,
            institution_id=inst.id,
            reference_month=8,
            reference_year=2026,
            due_date=date(2026, 8, 10),
            total_amount=120.0,
        )
        self.db.add(inv)
        self.db.flush()

        item = InvoiceItem(
            invoice_id=inv.id,
            category_id=cat_desconhecido.id,
            purchase_date=date(2026, 8, 2),
            description="PARQUE TEMATICO AVENTURA",
            amount=120.0,
        )
        self.db.add(item)
        self.db.commit()

        # Usuário reclassifica para "Lazer / Entretenimento"
        CategorizerService.reclassify_item(
            db=self.db,
            user_id=self.user.id,
            item_id=item.id,
            new_category_id=cat_lazer.id,
            apply_to_future=True,
        )

        # Verifica se o item atualizou
        self.assertEqual(item.category_id, cat_lazer.id)

        # Verifica se o sistema aprendeu e aplica em novas faturas (RN-05)
        nova_classificacao = CategorizerService.categorize(self.db, self.user.id, "COMPRA PARQUE TEMATICO AVENTURA INGRESSO")
        self.assertEqual(
            nova_classificacao.name,
            "Lazer / Entretenimento",
            "FALHA NO APRENDIZADO POR REFORÇO: O sistema não priorizou a regra memorizada do usuário!"
        )

        # Limpeza
        self.db.delete(item)
        self.db.delete(inv)
        self.db.commit()

    # -------------------------------------------------------------
    # 4. AUDITORIA RN-02: Prevenção de Duplicidade de Faturas
    # -------------------------------------------------------------
    def test_rn02_invoice_duplication_prevention(self):
        """Audita a rejeição de faturas duplicadas para o mesmo período e emissor."""
        inst = self.db.query(Institution).filter_by(slug="caixa").first()
        
        inv1 = Invoice(
            user_id=self.user.id,
            institution_id=inst.id,
            reference_month=9,
            reference_year=2026,
            due_date=date(2026, 9, 20),
            total_amount=350.0,
        )
        self.db.add(inv1)
        self.db.commit()

        # Tentativa de inserir duplicada para a mesma competência
        inv_duplicada = Invoice(
            user_id=self.user.id,
            institution_id=inst.id,
            reference_month=9,
            reference_year=2026,
            due_date=date(2026, 9, 20),
            total_amount=350.0,
        )
        self.db.add(inv_duplicada)
        with self.assertRaises(Exception):
            self.db.commit()
        
        self.db.rollback()

        # Limpeza
        self.db.delete(inv1)
        self.db.commit()

    # -------------------------------------------------------------
    # 5. AUDITORIA US-07 & RN-03: Projeções Futuras de Parcelas
    # -------------------------------------------------------------
    def test_us07_rn03_projections_engine(self):
        """
        Audita a precisão matemática da RN-03:
        Compra com parcela 03/06 em Outubro/2026 no valor de R$ 200,00:
        - Deve projetar Novembro/2026 (04/06): R$ 200,00
        - Deve projetar Dezembro/2026 (05/06): R$ 200,00
        - Deve projetar Janeiro/2027 (06/06): R$ 200,00
        - Total comprometido futuro: R$ 600,00
        - A partir de Fevereiro/2027: Parcela encerrada.
        """
        inst = self.db.query(Institution).filter_by(slug="nubank").first()
        cat = self.db.query(Category).first()

        # Limpa qualquer resíduo anterior de teste
        existing_test_inv = self.db.query(Invoice).filter_by(
            user_id=self.user_b.id,
            institution_id=inst.id,
            reference_month=10,
            reference_year=2026
        ).first()
        if existing_test_inv:
            self.db.delete(existing_test_inv)
            self.db.commit()

        inv = Invoice(
            user_id=self.user_b.id,
            institution_id=inst.id,
            reference_month=10,
            reference_year=2026,
            due_date=date(2026, 10, 25),
            total_amount=200.0,
        )
        self.db.add(inv)
        self.db.flush()

        item = InvoiceItem(
            invoice_id=inv.id,
            category_id=cat.id,
            purchase_date=date(2026, 10, 5),
            description="NOTEBOOK TRABALHO",
            amount=200.0,
            current_installment=3,
            total_installments=6,
        )
        self.db.add(item)
        self.db.commit()

        proj_result = ProjectionService.calculate_future_projections(self.db, self.user_b.id, months_ahead=6)
        projections = proj_result["projections"]
        
        # Filtra os meses projetados para este compromisso
        proj_map = {p["period"]: p for p in projections}

        self.assertIn("2026-11", proj_map)
        self.assertIn("2026-12", proj_map)
        self.assertIn("2027-01", proj_map)
        
        # O compromisso específico 'NOTEBOOK TRABALHO' encerra em 2027-01 (06/06) e não pode constar em 2027-02
        if "2027-02" in proj_map:
            notebook_in_feb = [c for c in proj_map["2027-02"]["commitments"] if c["description"] == "NOTEBOOK TRABALHO"]
            self.assertEqual(len(notebook_in_feb), 0, "RN-03: O compromisso não deve constar após a quitação total!")

        # Validação do valor em cada mês
        for p_key in ["2026-11", "2026-12", "2027-01"]:
            month_entry = proj_map[p_key]
            matching_comm = [c for c in month_entry["commitments"] if c["description"] == "NOTEBOOK TRABALHO"]
            self.assertEqual(len(matching_comm), 1)
            self.assertEqual(matching_comm[0]["amount"], 200.0)

        # Limpeza
        self.db.delete(item)
        self.db.delete(inv)
        self.db.commit()

    # -------------------------------------------------------------
    # 6. AUDITORIA US-06: Indicadores e Métricas de BI
    # -------------------------------------------------------------
    def test_us06_analytics_service_kpis(self):
        """Audita a geração de dados analíticos para os cards de KPI e gráficos."""
        inst = self.db.query(Institution).filter_by(slug="itau").first()
        cat_alim = self.db.query(Category).filter_by(name="Alimentação").first()
        cat_comb = self.db.query(Category).filter_by(name="Transporte / Combustível").first()

        # Fatura 1 (mês anterior) = R$ 1000
        inv1 = Invoice(
            user_id=self.user.id,
            institution_id=inst.id,
            reference_month=5,
            reference_year=2026,
            due_date=date(2026, 5, 10),
            total_amount=1000.0,
        )
        self.db.add(inv1)

        # Fatura 2 (mês atual) = R$ 1200 (+20%)
        inv2 = Invoice(
            user_id=self.user.id,
            institution_id=inst.id,
            reference_month=6,
            reference_year=2026,
            due_date=date(2026, 6, 10),
            total_amount=1200.0,
        )
        self.db.add(inv2)
        self.db.flush()

        item1 = InvoiceItem(invoice_id=inv2.id, category_id=cat_alim.id, purchase_date=date(2026, 6, 1), description="IFOOD", amount=800.0)
        item2 = InvoiceItem(invoice_id=inv2.id, category_id=cat_comb.id, purchase_date=date(2026, 6, 2), description="POSTO", amount=400.0)
        self.db.add_all([item1, item2])
        self.db.commit()

        bi_data = AnalyticsService.get_dashboard_data(self.db, self.user.id, institution_slug="itau", year=2026, month=6)
        
        self.assertTrue(bi_data["has_data"])
        self.assertEqual(bi_data["kpis"]["current_total"], 1200.0)
        self.assertEqual(bi_data["kpis"]["previous_total"], 1000.0)
        self.assertEqual(bi_data["kpis"]["percentage_change"], 20.0)  # +20%
        self.assertEqual(bi_data["kpis"]["top_category"]["name"], "Alimentação")
        self.assertEqual(bi_data["kpis"]["top_category"]["amount"], 800.0)

        # Limpeza
        self.db.delete(item1)
        self.db.delete(item2)
        self.db.delete(inv2)
        self.db.delete(inv1)
        self.db.commit()

if __name__ == "__main__":
    unittest.main()
