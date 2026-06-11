import uuid
from datetime import datetime
from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ScanType(StrEnum):
    SUBDOMAIN_ENUM = "subdomain_enum"
    HTTP_PROBE = "http_probe"
    PORT_SCAN = "port_scan"
    HEADER_CHECK = "header_check"
    CLICKJACKING = "clickjacking"
    DOMAIN_SPOOFING = "domain_spoofing"
    TLS_SCAN = "tls_scan"
    CONTENT_FUZZ = "content_fuzz"
    GIT_DUMP = "git_dump"
    NUCLEI_SCAN = "nuclei_scan"


class ScanStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("targets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scan_type: Mapped[ScanType] = mapped_column(
        sa.Enum(ScanType, name="scantype", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    status: Mapped[ScanStatus] = mapped_column(
        sa.Enum(ScanStatus, name="scanstatus", values_callable=lambda x: [e.value for e in x]),
        default=ScanStatus.PENDING,
        nullable=False,
    )
    error: Mapped[str | None] = mapped_column(sa.Text)
    started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    target: Mapped["Target"] = relationship(back_populates="scans")
    results: Mapped[list["ScanResult"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )
