import uuid
from sqlalchemy import Column, String, Integer, Float, Date, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from src.core.database import Base

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=False, index=True)

    purchase_date = Column(Date, nullable=False, index=True)
    description = Column(String(255), nullable=False)
    raw_text = Column(String(500), nullable=True)
    amount = Column(Float, nullable=False)
    
    current_installment = Column(Integer, nullable=False, default=1)
    total_installments = Column(Integer, nullable=False, default=1)
    is_recurring = Column(Boolean, nullable=False, default=False)

    invoice = relationship("Invoice", back_populates="items")
    category = relationship("Category", back_populates="invoice_items")

    __table_args__ = (
        Index("ix_items_invoice_purchase", "invoice_id", "purchase_date"),
    )
