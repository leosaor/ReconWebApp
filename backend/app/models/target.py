import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Target(Base):
    __tablename__ = "targets"
    __table_args__ = (sa.UniqueConstraint("project_id", "value", name="uq_target_project_value"),)

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    value: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    kind: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="domain")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="targets")
    scans: Mapped[list["Scan"]] = relationship(
        back_populates="target", cascade="all, delete-orphan"
    )
