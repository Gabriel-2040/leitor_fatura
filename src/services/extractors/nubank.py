import io
import re
from datetime import date, datetime
import pdfplumber
from src.services.extractors.base import BaseInvoiceExtractor, ExtractedInvoiceDTO, ExtractedItemDTO

class NubankExtractor(BaseInvoiceExtractor):
    """Extrator especializado para faturas em PDF do Nubank (Roxinho / Ultravioleta)."""

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

        # 1. Extração de Metadados (Vencimento, Fechamento e Total)
        due_date, closing_date, total_amount, ref_month, ref_year = self._extract_metadata(extracted_text)

        # 2. Extração de Itens Lançados
        items = []
        for line in lines:
            item = self._parse_line(line, default_year=ref_year)
            if item:
                items.append(item)

        # Se total_amount não foi encontrado no cabeçalho, calcula pela soma
        if total_amount == 0.0 and items:
            total_amount = round(sum(i.amount for i in items), 2)

        return ExtractedInvoiceDTO(
            institution_slug="nubank",
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

        # Procura Vencimento: "VENCIMENTO 25 JAN 2026" ou "Vencimento: 25/01/2026"
        due_match = re.search(
            r'(?:VENCIMENTO|Vencimento|Data de vencimento)[:\s]+(\d{1,2})\s+([A-Za-zç]{3,9}|\d{1,2})(?:\s+|[/\-])(\d{4})?',
            full_text,
            re.IGNORECASE
        )
        if due_match:
            d = int(due_match.group(1))
            m_raw = due_match.group(2).lower()[:3]
            m = self.MONTHS_MAP.get(m_raw) if not m_raw.isdigit() else int(m_raw)
            y = int(due_match.group(3)) if due_match.group(3) else today.year
            if m:
                try:
                    due_date = date(y, m, d)
                    ref_year = y
                    ref_month = m
                except ValueError:
                    pass

        # Fechamento (se houver menção)
        close_match = re.search(
            r'(?:FECHAMENTO|Fechamento)[:\s]+(\d{1,2})[/\.\-](\d{1,2})(?:[/\.\-](\d{2,4}))?',
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

        # Total da Fatura: "Total a pagar R$ 1.250,00" ou "Valor total R$ 1.250,00"
        tot_match = re.search(
            r'(?:TOTAL A PAGAR|TOTAL DA FATURA|VALOR TOTAL|TOTAL)[:\s]+(?:R\$\s*)?([\d\.,]+)',
            full_text,
            re.IGNORECASE
        )
        if tot_match:
            total_amount = self.parse_currency(tot_match.group(1))

        return due_date, closing_date, total_amount, ref_month, ref_year

    def _parse_line(self, line: str, default_year: int) -> ExtractedItemDTO | None:
        """
        Padrões Nubank típicos:
        - 12 JAN Mercado Livre 01/03 45,90
        - 15/01 Netflix 55,90
        - 20 JAN Pagamento recebido -1.200,00 (ignorado ou registrado como crédito)
        """
        # Ignora linhas de cabeçalho ou metadados
        if any(keyword in line.upper() for keyword in ["TOTAL", "PAGAMENTO EM", "RESUMO DA FATURA", "VENCIMENTO", "LIMITE", "SALDO"]):
            return None

        # Regex: Data inicial (DD MMM ou DD/MM) + Descrição + Valor no final
        pattern = re.match(
            r'^(\d{1,2}\s+[A-Za-zç]{3,9}|\d{1,2}/\d{1,2})\s+(.+?)\s+([R\$\s]*[\-\+]?[\d\.,]+)$',
            line,
            re.IGNORECASE
        )
        if not pattern:
            return None

        date_raw = pattern.group(1).strip()
        desc_raw = pattern.group(2).strip()
        val_raw = pattern.group(3).strip()

        parsed_date = self.parse_date(date_raw, default_year=default_year)
        if not parsed_date:
            return None

        amount = self.parse_currency(val_raw)
        if amount == 0.0:
            return None

        # Detecta parcelamento
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
