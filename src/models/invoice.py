import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from src.core.database import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    
    reference_month = Column(Integer, nullable=False)  # 1 a 12
    reference_year = Column(Integer, nullable=False)   # Ex: 2026
    closing_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=False)
    total_amount = Column(Float, nullable=False, default=0.0)
    file_hash = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="invoices")
    institution = relationship("Institution", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "institution_id", "reference_month", "reference_year", name="uq_user_inst_period"),
    )
