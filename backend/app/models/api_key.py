import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    # Prefixo exibível (primeiros 16 chars da chave raw, ex: "rwa_Abc123456789")
    prefix: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    hashed_key: Mapped[str] = mapped_column(sa.String(64), unique=True, nullable=False)
    revoked: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="api_keys")
