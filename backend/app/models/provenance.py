from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

class Provenance(Base):
    __tablename__ = "provenance"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[str] = mapped_column(String(64), index=True)
    claim_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_id: Mapped[str] = mapped_column(String(32), index=True)
    evidence: Mapped[str] = mapped_column(Text)
