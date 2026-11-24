import io
import re
from datetime import date
from typing import Optional
import pdfplumber
from src.services.extractors.base import BaseInvoiceExtractor, ExtractedInvoiceDTO, ExtractedItemDTO

class BradescoExtractor(BaseInvoiceExtractor):
    """Extrator especializado para faturas em PDF do Bradesco / Bradescard."""

    def extract(self, pdf_bytes: bytes) -> ExtractedInvoiceDTO:
        extracted_text = ""
        lines = []

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=False) or ""
                extracted_text += "\n" + text
                for line in text.split("\n"):
                    line_clean = line.strip()
                    if line_clean:
                        lines.append(line_clean)

        due_date, closing_date, total_amount, ref_month, ref_year = self._extract_metadata(extracted_text)

        items = []
        for line in lines:
            item = self._parse_line(line, default_year=ref_year)
            if item:
                items.append(item)

        if total_amount == 0.0 and items:
            total_amount = round(sum(i.amount for i in items if i.amount > 0), 2)

        return ExtractedInvoiceDTO(
            institution_slug="bradesco",
            reference_month=ref_month,
            reference_year=ref_year,
            due_date=due_date,
            closing_date=closing_date,
            total_amount=total_amount,
            items=items,
        )

    def _extract_metadata(self, full_text: str):
        today = date.today()
        due_date = today
        closing_date = None
        total_amount = 0.0
        ref_year = today.year
        ref_month = today.month

        # Vencimento Bradesco: "Vencimento: 15/02/2026" ou "DATA DE VENCIMENTO 15/02/2026"
        due_match = re.search(
            r'(?:DATA DE VENCIMENTO|Vencimento)[:\s]+(\d{1,2})[/\.\-](\d{1,2})(?:[/\.\-](\d{2,4}))?',
            full_text,
            re.IGNORECASE
        )
        if due_match:
            d = int(due_match.group(1))
            m = int(due_match.group(2))
            y = int(due_match.group(3)) if due_match.group(3) else today.year
            if y < 100:
                y += 2000
            try:
                due_date = date(y, m, d)
                ref_year = y
                ref_month = m
            except ValueError:
                pass

        # Total da Fatura Bradesco: "Total da Fatura: R$ 4.100,50" ou "Total desta fatura"
        tot_match = re.search(
            r'(?:Total da Fatura|Total desta fatura|Total a pagar|Saldo atual)[:\s]+(?:R\$\s*)?([\d\.,]+)',
            full_text,
            re.IGNORECASE
        )
        if tot_match:
            total_amount = self.parse_currency(tot_match.group(1))

        # Fechamento / Corte:
        close_match = re.search(
            r'(?:Data de Fechamento|Melhor dia|Data de corte)[:\s]+(\d{1,2})[/\.\-](\d{1,2})(?:[/\.\-](\d{2,4}))?',
            full_text,
            re.IGNORECASE
        )
        if close_match:
            d = int(close_match.group(1))
            m = int(close_match.group(2))
            y = int(close_match.group(3)) if close_match.group(3) else ref_year
            if y < 100:
                y += 2000
            try:
                closing_date = date(y, m, d)
            except ValueError:
                pass

        return due_date, closing_date, total_amount, ref_month, ref_year

    def _parse_line(self, line: str, default_year: int) -> Optional[ExtractedItemDTO]:
        if any(keyword in line.upper() for keyword in ["TOTAL", "SUBTOTAL", "SALDO ANTERIOR", "PAGTO EFETUADO", "AUTORIZACAO"]):
            return None

        # Padrão Bradesco: 10/02 LOJAS AMERICANAS 02/05 59,90 ou com letra D/C no final
        pattern = re.match(
            r'^(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s+(.+?)\s+([R\$\s]*[\-\+]?[\d\.,]+(?:\s*[DC])?)$',
            line,
            re.IGNORECASE
        )
        if not pattern:
            return None

        date_raw = pattern.group(1).strip()
        desc_raw = pattern.group(2).strip()
        val_raw = pattern.group(3).strip()

        is_credit = "C" in val_raw.upper()
        clean_val_str = re.sub(r'[DCdc]', '', val_raw).strip()

        parsed_date = self.parse_date(date_raw, default_year=default_year)
        if not parsed_date:
            return None

        amount = self.parse_currency(clean_val_str)
        if is_credit and amount > 0:
            amount = -amount

        if amount == 0.0:
            return None

        curr_parc, tot_parc, clean_desc = self.extract_installment(desc_raw)

        return ExtractedItemDTO(
            purchase_date=parsed_date,
            description=clean_desc.strip(),
            amount=amount,
            current_installment=curr_parc,
            total_installments=tot_parc,
            is_recurring=False,
            raw_text=line,
        )
