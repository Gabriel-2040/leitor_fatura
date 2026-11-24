import hashlib
from typing import Optional, List
from sqlalchemy.orm import Session
from src.models.invoice import Invoice
from src.models.invoice_item import InvoiceItem
from src.models.institution import Institution
from src.services.extractors.factory import ExtractorFactory
from src.services.categorizer import CategorizerService

class InvoiceService:
    @staticmethod
    def calculate_file_hash(pdf_bytes: bytes) -> str:
        """Calcula o hash SHA-256 do arquivo para auditoria e controle de integridade."""
        return hashlib.sha256(pdf_bytes).hexdigest()

    @classmethod
    def process_and_save_invoice(
        cls,
        db: Session,
        user_id: str,
        institution_slug: str,
        pdf_bytes: bytes,
        allow_overwrite: bool = False
    ) -> Invoice:
        """
        Executa o pipeline completo:
        1. Localiza a instituição pelo slug.
        2. Executa o extrator especializado.
        3. Valida duplicidade de fatura (RN-02).
        4. Categoriza os itens (RN-05).
        5. Persiste a fatura e lançamentos.
        """
        # 1. Localiza a instituição
        institution = db.query(Institution).filter(Institution.slug == institution_slug.lower()).first()
        if not institution:
            raise ValueError(f"Instituição '{institution_slug}' não cadastrada.")

        # 2. Aciona o extrator especializado
        extractor = ExtractorFactory.get_extractor(institution.slug)
        extracted_data = extractor.extract(pdf_bytes)

        # 3. Prevenção de duplicidade (RN-02)
        existing = (
            db.query(Invoice)
            .filter(
                Invoice.user_id == user_id,
                Invoice.institution_id == institution.id,
                Invoice.reference_month == extracted_data.reference_month,
                Invoice.reference_year == extracted_data.reference_year,
            )
            .first()
        )

        if existing:
            if not allow_overwrite:
                raise ValueError(
                    f"A fatura de {institution.name} referente a "
                    f"{extracted_data.reference_month:02d}/{extracted_data.reference_year} "
                    f"já foi importada anteriormente."
                )
            else:
                db.delete(existing)
                db.commit()

        file_hash = cls.calculate_file_hash(pdf_bytes)

        # 4. Criação do cabeçalho da Fatura
        invoice = Invoice(
            user_id=user_id,
            institution_id=institution.id,
            reference_month=extracted_data.reference_month,
            reference_year=extracted_data.reference_year,
            closing_date=extracted_data.closing_date,
            due_date=extracted_data.due_date,
            total_amount=extracted_data.total_amount,
            file_hash=file_hash,
        )
        db.add(invoice)
        db.flush()  # Obtém o invoice.id antes dos itens

        # 5. Categorização e criação de itens
        for item_dto in extracted_data.items:
            category = CategorizerService.categorize(
                db=db,
                user_id=user_id,
                description=item_dto.description,
            )

            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                category_id=category.id,
                purchase_date=item_dto.purchase_date,
                description=item_dto.description,
                raw_text=item_dto.raw_text,
                amount=item_dto.amount,
                current_installment=item_dto.current_installment,
                total_installments=item_dto.total_installments,
                is_recurring=item_dto.is_recurring,
            )
            db.add(invoice_item)

        db.commit()
        db.refresh(invoice)
        return invoice

    @classmethod
    def list_invoices(
        cls,
        db: Session,
        user_id: str,
        institution_slug: Optional[str] = None,
        year: Optional[int] = None
    ) -> List[Invoice]:
        """Lista faturas do usuário com filtros opcionais de emissor e ano."""
        query = db.query(Invoice).filter(Invoice.user_id == user_id)
        if institution_slug and institution_slug != "all":
            query = query.join(Institution).filter(Institution.slug == institution_slug)
        if year:
            query = query.filter(Invoice.reference_year == year)
        return query.order_by(Invoice.reference_year.desc(), Invoice.reference_month.desc()).all()

    @classmethod
    def get_invoice_by_id(cls, db: Session, user_id: str, invoice_id: str) -> Optional[Invoice]:
        return db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.user_id == user_id).first()

    @classmethod
    def delete_invoice(cls, db: Session, user_id: str, invoice_id: str) -> bool:
        invoice = cls.get_invoice_by_id(db, user_id, invoice_id)
        if invoice:
            db.delete(invoice)
            db.commit()
            return True
        return False
