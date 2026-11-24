from datetime import date
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from src.models.invoice import Invoice
from src.models.invoice_item import InvoiceItem

class ProjectionService:
    @staticmethod
    def _add_months(year: int, month: int, delta: int) -> tuple[int, int]:
        """Calcula o ano e mês resultantes da adição de delta meses."""
        total_months = year * 12 + (month - 1) + delta
        new_year = total_months // 12
        new_month = (total_months % 12) + 1
        return new_year, new_month

    @classmethod
    def calculate_future_projections(
        cls,
        db: Session,
        user_id: str,
        months_ahead: int = 12
    ) -> Dict[str, Any]:
        """
        Calcula as projeções financeiras futuras baseadas em compras parceladas ativas.
        Aplica a RN-03 do PRD.
        """
        # 1. Busca todos os itens parcelados do usuário
        items = (
            db.query(InvoiceItem)
            .join(Invoice)
            .filter(
                Invoice.user_id == user_id,
                InvoiceItem.total_installments > 1,
            )
            .order_by(Invoice.reference_year.desc(), Invoice.reference_month.desc())
            .all()
        )

        # 2. Identifica o estado mais recente de cada compra parcelada
        # Chave de unicidade do compromisso: (descrição limpa, valor, total_installments)
        latest_commitments = {}

        for item in items:
            key = (item.description.strip().upper(), round(item.amount, 2), item.total_installments)
            if key not in latest_commitments:
                latest_commitments[key] = {
                    "item": item,
                    "invoice_year": item.invoice.reference_year,
                    "invoice_month": item.invoice.reference_month,
                    "current_installment": item.current_installment,
                    "total_installments": item.total_installments,
                    "amount": item.amount,
                    "category_name": item.category.name if item.category else "Outros",
                    "category_color": item.category.color_hex if item.category else "#94A3B8",
                }

        # 3. Mapeia faturas já existentes no banco para não duplicar projeções
        existing_invoices = (
            db.query(Invoice.reference_year, Invoice.reference_month)
            .filter(Invoice.user_id == user_id)
            .all()
        )
        existing_periods = {f"{y:04d}-{m:02d}" for y, m in existing_invoices}

        # 4. Projeta os meses futuros para cada compra
        projections_map: Dict[str, Dict[str, Any]] = {}

        for key, comm in latest_commitments.items():
            curr_inst = comm["current_installment"]
            tot_inst = comm["total_installments"]
            remaining = tot_inst - curr_inst

            if remaining <= 0:
                continue

            base_year = comm["invoice_year"]
            base_month = comm["invoice_month"]

            for step in range(1, remaining + 1):
                proj_year, proj_month = cls._add_months(base_year, base_month, step)
                period_str = f"{proj_year:04d}-{proj_month:02d}"
                projected_inst_num = curr_inst + step

                if period_str not in projections_map:
                    projections_map[period_str] = {
                        "period": period_str,
                        "year": proj_year,
                        "month": proj_month,
                        "total_projected": 0.0,
                        "items_count": 0,
                        "has_existing_invoice": period_str in existing_periods,
                        "commitments": [],
                    }

                projections_map[period_str]["total_projected"] += comm["amount"]
                projections_map[period_str]["items_count"] += 1
                projections_map[period_str]["commitments"].append({
                    "description": comm["item"].description,
                    "installment": f"{projected_inst_num:02d}/{tot_inst:02d}",
                    "amount": round(comm["amount"], 2),
                    "category": comm["category_name"],
                    "color": comm["category_color"],
                })

        # 5. Ordena cronologicamente os períodos projetados
        sorted_periods = sorted(projections_map.keys())
        # Limita ao número de meses solicitado
        if months_ahead:
            sorted_periods = sorted_periods[:months_ahead]

        projections_list = []
        grand_total_committed = 0.0

        for p in sorted_periods:
            entry = projections_map[p]
            entry["total_projected"] = round(entry["total_projected"], 2)
            grand_total_committed += entry["total_projected"]
            projections_list.append(entry)

        return {
            "total_committed": round(grand_total_committed, 2),
            "projections": projections_list,
        }
