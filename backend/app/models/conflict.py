from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

class Conflict(Base):
    __tablename__ = "conflicts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[str] = mapped_column(String(64), index=True)
    field: Mapped[str] = mapped_column(String(255))
    source_a: Mapped[str] = mapped_column(String(32))
    value_a: Mapped[str] = mapped_column(Text)
    source_b: Mapped[str] = mapped_column(String(32))
    value_b: Mapped[str] = mapped_column(Text)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="UNRESOLVED")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
