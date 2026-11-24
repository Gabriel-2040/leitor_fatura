import uuid
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from src.core.database import Base

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, index=True, nullable=False)
    color_hex = Column(String(7), nullable=False, default="#6366F1")

    invoices = relationship("Invoice", back_populates="institution")
