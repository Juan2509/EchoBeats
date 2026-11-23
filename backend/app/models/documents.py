"""Legacy tables retained so Alembic can compare the deployed schema."""

from sqlalchemy import CheckConstraint, UniqueConstraint, Column, DateTime, ForeignKey, Integer, LargeBinary, String, Table, Text, Uuid, func

from app.models.catalog import metadata
from app.models.vector import Vector1536

document = Table(
    "document", metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", String(200), nullable=False),
    Column("sha256", String(64), nullable=False),
    Column("status", String(16), nullable=False),
    Column("attempt", Uuid),
    Column("error", String(100)),
    Column("model_key", String(200)),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint("status IN ('pending','processing','ready','failed')", name="status"),
)

upload = Table(
    "document_upload", metadata,
    Column("document_id", Uuid, ForeignKey("document.id", ondelete="CASCADE"), primary_key=True),
    Column("pdf", LargeBinary, nullable=False),
)

chunk = Table(
    "document_chunk", metadata,
    Column("id", Uuid, primary_key=True),
    Column("document_id", Uuid, ForeignKey("document.id", ondelete="CASCADE"), nullable=False),
    Column("page", Integer, nullable=False),
    Column("ordinal", Integer, nullable=False),
    Column("section", String(200)),
    Column("extraction", String(8), nullable=False),
    Column("content", Text, nullable=False),
    Column("embedding", Vector1536(), nullable=False),
    UniqueConstraint("document_id", "page", "ordinal", name="uq_document_chunk_position"),
)
