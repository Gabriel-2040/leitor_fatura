from typing import Dict, Type
from src.services.extractors.base import BaseInvoiceExtractor
from src.services.extractors.nubank import NubankExtractor
from src.services.extractors.itau import ItauExtractor
from src.services.extractors.bradesco import BradescoExtractor
from src.services.extractors.caixa import CaixaExtractor

class ExtractorFactory:
    """Fábrica de Extratores de Fatura (Strategy Pattern)."""

    _EXTRACTORS: Dict[str, Type[BaseInvoiceExtractor]] = {
        "nubank": NubankExtractor,
        "itau": ItauExtractor,
        "bradesco": BradescoExtractor,
        "caixa": CaixaExtractor,
    }

    @classmethod
    def get_extractor(cls, institution_slug: str) -> BaseInvoiceExtractor:
        slug = institution_slug.strip().lower()
        extractor_cls = cls._EXTRACTORS.get(slug)
        if not extractor_cls:
            supported = ", ".join(cls._EXTRACTORS.keys())
            raise ValueError(f"Instituição '{institution_slug}' não suportada. Suportadas: {supported}")
        return extractor_cls()

    @classmethod
    def supported_institutions(cls) -> list[str]:
        return list(cls._EXTRACTORS.keys())
