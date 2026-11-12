"""Procedencia de álbum y portada individual sin contaminar el álbum desconocido."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003_metadata"
down_revision = "0002_catalog"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("album", sa.Column("import_key", sa.String(64)))
    op.create_unique_constraint("uq_album_import_key", "album", ["import_key"])
    op.add_column("album", sa.Column("metadata_sources", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("track", sa.Column("cover_asset_id", sa.Uuid()))
    op.create_foreign_key("fk_track_cover_asset_id_media_asset", "track", "media_asset", ["cover_asset_id"], ["id"], ondelete="RESTRICT")


def downgrade():
    op.drop_constraint("fk_track_cover_asset_id_media_asset", "track", type_="foreignkey")
    op.drop_column("track", "cover_asset_id")
    op.drop_column("album", "metadata_sources")
    op.drop_constraint("uq_album_import_key", "album", type_="unique")
    op.drop_column("album", "import_key")
