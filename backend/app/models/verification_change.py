from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

class VerificationChange(Base):
    __tablename__ = 'verification_changes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[str] = mapped_column(String(64), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    section: Mapped[str] = mapped_column(String(255), default='Document')
    location: Mapped[str] = mapped_column(String(255), default='')
    previous_value: Mapped[str] = mapped_column(Text)
    current_value: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default='PENDING')
    decided_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
