from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
import io
import re
from typing import Optional, List, Tuple

@dataclass
class ExtractedItemDTO:
    purchase_date: date
    description: str
    amount: float
    current_installment: int = 1
    total_installments: int = 1
    is_recurring: bool = False
    raw_text: str = ""

@dataclass
class ExtractedInvoiceDTO:
    institution_slug: str
    reference_month: int
    reference_year: int
    due_date: date
    closing_date: Optional[date] = None
    total_amount: float = 0.0
    items: List[ExtractedItemDTO] = field(default_factory=list)

class BaseInvoiceExtractor(ABC):
    """Classe base abstrata para extratores especializados de faturas em PDF."""

    MONTHS_MAP = {
        "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
        "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
        "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
        "outubro": 10, "novembro": 11, "dezembro": 12,
    }

    @abstractmethod
    def extract(self, pdf_bytes: bytes) -> ExtractedInvoiceDTO:
        """Processa o binário do PDF e extrai os dados estruturados."""
        pass

    @staticmethod
    def parse_currency(value_str: str) -> float:
        """Converte strings monetárias brasileiras (ex: 'R$ 1.250,45', '45,90', '-10,00', '15,00-') em float."""
        if not value_str:
            return 0.0
        
        cleaned = value_str.strip().replace("R$", "").replace("r$", "").replace(" ", "")
        is_negative = "-" in cleaned or "CR" in cleaned.upper() or cleaned.endswith("-")
        cleaned = cleaned.replace("CR", "").replace("cr", "").replace("-", "")

        # Remove separador de milhar (.) e substitui vírgula decimal por ponto
        cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            val = float(cleaned)
            return -val if is_negative else val
        except ValueError:
            return 0.0

    @staticmethod
    def extract_installment(text: str) -> Tuple[int, int, str]:
        """
        Detecta marcações de parcelamento como '01/10', '2/6', 'PARC 03/12', 'PARC 01 DE 05'.
        Retorna (parcela_atual, total_parcelas, descricao_limpa).
        """
        # Padrão 1: 01/06 ou 1/6
        match = re.search(r'(?:PARC(?:ELA)?\.?\s*)?(\d{1,2})\s*/\s*(\d{1,2})', text, re.IGNORECASE)
        if match:
            current = int(match.group(1))
            total = int(match.group(2))
            clean_text = re.sub(r'(?:PARC(?:ELA)?\.?\s*)?\d{1,2}\s*/\s*\d{1,2}', '', text, flags=re.IGNORECASE).strip()
            # Limpa traços ou pontuações órfãs
            clean_text = re.sub(r'[\s\-]+$', '', clean_text).strip()
            return current, total, clean_text

        # Padrão 2: 01 DE 06 ou PARCELA 2 DE 10
        match_de = re.search(r'(?:PARC(?:ELA)?\.?\s*)?(\d{1,2})\s+DE\s+(\d{1,2})', text, re.IGNORECASE)
        if match_de:
            current = int(match_de.group(1))
            total = int(match_de.group(2))
            clean_text = re.sub(r'(?:PARC(?:ELA)?\.?\s*)?\d{1,2}\s+DE\s+\d{1,2}', '', text, flags=re.IGNORECASE).strip()
            clean_text = re.sub(r'[\s\-]+$', '', clean_text).strip()
            return current, total, clean_text

        return 1, 1, text.strip()

    @staticmethod
    def parse_date(date_str: str, default_year: int) -> Optional[date]:
        """Interpreta datas no formato DD/MM, DD/MM/AAAA ou DD MMM."""
        date_str = date_str.strip()
        
        # Formato DD/MM/YYYY ou DD/MM/YY
        match_full = re.match(r'^(\d{1,2})[/\.\-](\d{1,2})[/\.\-](\d{2,4})$', date_str)
        if match_full:
            d, m, y = int(match_full.group(1)), int(match_full.group(2)), int(match_full.group(3))
            if y < 100:
                y += 2000
            try:
                return date(y, m, d)
            except ValueError:
                return None

        # Formato DD/MM
        match_dm = re.match(r'^(\d{1,2})[/\.\-](\d{1,2})$', date_str)
        if match_dm:
            d, m = int(match_dm.group(1)), int(match_dm.group(2))
            try:
                return date(default_year, m, d)
            except ValueError:
                return None

        # Formato DD MMM (ex: 15 JAN)
        match_d_mmm = re.match(r'^(\d{1,2})\s+([A-Za-zç]{3,9})$', date_str, re.IGNORECASE)
        if match_d_mmm:
            d = int(match_d_mmm.group(1))
            month_name = match_d_mmm.group(2).lower()[:3]
            m = BaseInvoiceExtractor.MONTHS_MAP.get(month_name)
            if m:
                try:
                    return date(default_year, m, d)
                except ValueError:
                    return None

        return None
