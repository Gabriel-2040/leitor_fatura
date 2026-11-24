from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.invoice import Invoice
from src.models.invoice_item import InvoiceItem
from src.models.category import Category
from src.models.institution import Institution

class AnalyticsService:
    @classmethod
    def get_dashboard_data(
        cls,
        db: Session,
        user_id: str,
        institution_slug: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Retorna todos os dados analíticos necessários para alimentar o Painel BI:
        - KPIs consolidados
        - Distribuição por macrocategoria
        - Série histórica de faturas
        - Lista detalhada de itens
        """
        # 1. Filtro base de faturas
        invoice_query = db.query(Invoice).filter(Invoice.user_id == user_id)
        if institution_slug and institution_slug != "all":
            invoice_query = invoice_query.join(Institution).filter(Institution.slug == institution_slug)

        invoices = invoice_query.order_by(Invoice.reference_year.desc(), Invoice.reference_month.desc()).all()

        if not invoices:
            return {
                "has_data": False,
                "kpis": {
                    "current_total": 0.0,
                    "previous_total": 0.0,
                    "percentage_change": 0.0,
                    "top_category": None,
                    "items_count": 0,
                },
                "by_category": [],
                "monthly_history": [],
                "items": [],
            }

        # 2. Determina a fatura ativa para visualização
        target_invoice = None
        if year and month:
            for inv in invoices:
                if inv.reference_year == year and inv.reference_month == month:
                    target_invoice = inv
                    break

        if not target_invoice:
            target_invoice = invoices[0]

        # 3. Localiza a fatura imediatamente anterior para cálculo de variação
        previous_invoice = None
        for inv in invoices:
            if (inv.reference_year < target_invoice.reference_year) or (
                inv.reference_year == target_invoice.reference_year and inv.reference_month < target_invoice.reference_month
            ):
                previous_invoice = inv
                break

        current_total = float(target_invoice.total_amount)
        previous_total = float(previous_invoice.total_amount) if previous_invoice else 0.0

        if previous_total > 0:
            percentage_change = round(((current_total - previous_total) / previous_total) * 100, 2)
        else:
            percentage_change = 0.0

        # 4. Agrupamento por Categoria da Fatura Ativa
        cat_stats = (
            db.query(
                Category.id,
                Category.name,
                Category.color_hex,
                Category.icon_name,
                func.sum(InvoiceItem.amount).label("total_amount"),
                func.count(InvoiceItem.id).label("items_count")
            )
            .join(InvoiceItem, InvoiceItem.category_id == Category.id)
            .filter(InvoiceItem.invoice_id == target_invoice.id)
            .group_by(Category.id, Category.name, Category.color_hex, Category.icon_name)
            .order_by(func.sum(InvoiceItem.amount).desc())
            .all()
        )

        by_category = []
        top_category = None
        sum_expenses = sum(row.total_amount for row in cat_stats if row.total_amount > 0)

        for row in cat_stats:
            amount = round(float(row.total_amount), 2)
            pct = round((amount / sum_expenses * 100), 2) if sum_expenses > 0 else 0.0
            cat_entry = {
                "id": row.id,
                "name": row.name,
                "color": row.color_hex,
                "icon": row.icon_name,
                "amount": amount,
                "percentage": pct,
                "items_count": row.items_count,
            }
            by_category.append(cat_entry)

        if by_category and by_category[0]["amount"] > 0:
            top_category = by_category[0]

        # 5. Histórico Cronológico das Faturas
        # Ordena do mais antigo para o mais recente
        history_invoices = sorted(invoices, key=lambda x: (x.reference_year, x.reference_month))
        monthly_history = [
            {
                "period": f"{inv.reference_year:04d}-{inv.reference_month:02d}",
                "label": f"{inv.reference_month:02d}/{inv.reference_year}",
                "amount": round(float(inv.total_amount), 2),
                "institution": inv.institution.name,
                "institution_slug": inv.institution.slug,
                "color": inv.institution.color_hex,
            }
            for inv in history_invoices
        ]

        # 6. Lançamentos da Fatura Ativa para exibição na tabela/editor
        items_data = [
            {
                "id": item.id,
                "date": item.purchase_date.strftime("%d/%m/%Y"),
                "description": item.description,
                "category_id": item.category_id,
                "category_name": item.category.name if item.category else "Outros",
                "category_color": item.category.color_hex if item.category else "#94A3B8",
                "amount": round(float(item.amount), 2),
                "installment": f"{item.current_installment:02d}/{item.total_installments:02d}" if item.total_installments > 1 else "À vista",
                "is_recurring": item.is_recurring,
            }
            for item in sorted(target_invoice.items, key=lambda x: x.purchase_date, reverse=True)
        ]

        return {
            "has_data": True,
            "target_invoice": {
                "id": target_invoice.id,
                "institution_name": target_invoice.institution.name,
                "institution_slug": target_invoice.institution.slug,
                "period": f"{target_invoice.reference_month:02d}/{target_invoice.reference_year}",
                "due_date": target_invoice.due_date.strftime("%d/%m/%Y"),
                "closing_date": target_invoice.closing_date.strftime("%d/%m/%Y") if target_invoice.closing_date else "-",
                "total_amount": current_total,
            },
            "kpis": {
                "current_total": current_total,
                "previous_total": previous_total,
                "percentage_change": percentage_change,
                "top_category": top_category,
                "items_count": len(items_data),
            },
            "by_category": by_category,
            "monthly_history": monthly_history,
            "items": items_data,
        }
