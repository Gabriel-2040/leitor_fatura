import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from src.core.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    color_hex = Column(String(7), nullable=False, default="#94A3B8")
    icon_name = Column(String(50), nullable=False, default="tag")
    is_default = Column(Boolean, default=True, nullable=False)

    invoice_items = relationship("InvoiceItem", back_populates="category")
    categorization_rules = relationship("CategorizationRule", back_populates="category")
