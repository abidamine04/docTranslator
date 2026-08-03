"""Add database-backed application and provider operational settings."""

import sqlalchemy as sa
from alembic import op

revision = "0002_database_backed_settings"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "application_settings" not in inspector.get_table_names():
        op.create_table(
        "application_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("default_target_language", sa.String(24), nullable=False),
        sa.Column("ocr_confidence_threshold", sa.Float(), nullable=False),
        sa.Column("max_upload_mb", sa.Integer(), nullable=False),
        sa.Column("max_page_count", sa.Integer(), nullable=False),
        sa.Column("file_retention_days", sa.Integer(), nullable=False),
        sa.Column("default_translation_tone", sa.String(50), nullable=False),
        sa.Column("translation_system_prompt", sa.Text(), nullable=False),
        sa.Column("storage_root", sa.Text(), nullable=False),
        sa.Column("language_detection_sample_chars", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    existing = {column["name"] for column in sa.inspect(bind).get_columns("provider_configurations")}
    additions = {
        "max_output_tokens": sa.Column("max_output_tokens", sa.Integer(), nullable=False, server_default="4096"),
        "chat_completions_path": sa.Column("chat_completions_path", sa.String(200), nullable=False, server_default="/chat/completions"),
        "models_path": sa.Column("models_path", sa.String(200), nullable=False, server_default="/models"),
        "translate_path": sa.Column("translate_path", sa.String(200), nullable=False, server_default="/translate"),
        "custom_headers": sa.Column("custom_headers", sa.JSON(), nullable=False, server_default="{}"),
        "verify_tls": sa.Column("verify_tls", sa.Boolean(), nullable=False, server_default=sa.true()),
    }
    for name, column in additions.items():
        if name not in existing:
            op.add_column("provider_configurations", column)


def downgrade() -> None:
    columns = (
        "verify_tls", "custom_headers", "translate_path", "models_path",
        "chat_completions_path", "max_output_tokens",
    )
    for column in columns:
        op.drop_column("provider_configurations", column)
    op.drop_table("application_settings")
