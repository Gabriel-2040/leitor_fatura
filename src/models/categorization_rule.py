import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from src.core.database import Base

class CategorizationRule(Base):
    __tablename__ = "categorization_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)

    pattern = Column(String(100), nullable=False, index=True)  # ex: "PADARIA REAL", "IFOOD"
    match_type = Column(String(20), nullable=False, default="CONTAINS")  # "EXACT", "CONTAINS", "REGEX"
    priority = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="categorization_rules")
    category = relationship("Category", back_populates="categorization_rules")

    __table_args__ = (
        Index("ix_rules_user_pattern", "user_id", "pattern"),
    )
