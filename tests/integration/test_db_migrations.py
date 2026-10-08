"""Database Migrations Integration Test Suite.

Validates Alembic configuration, migration scripts, revision history,
and schema metadata consistency.
"""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from backend.app.db.base import Base
from backend.migrations.versions.daede4011b68_initial_schema import downgrade, revision, upgrade


class TestDatabaseMigrations:
    """Validates Alembic migrations and schema metadata integrity."""

    def test_alembic_configuration_and_scripts(self):
        """Validates that alembic.ini points to valid migration directory and revisions."""
        root_dir = Path(__file__).resolve().parents[2]
        alembic_ini = root_dir / "backend" / "alembic.ini"
        assert alembic_ini.exists(), "backend/alembic.ini must exist"

        config = Config(str(alembic_ini))
        config.set_main_option("script_location", str(root_dir / "backend" / "migrations").replace("\\", "/"))
        config.set_main_option("version_locations", str(root_dir / "backend" / "migrations" / "versions").replace("\\", "/"))
        script = ScriptDirectory.from_config(config)

        # Get all revisions
        revisions = list(script.walk_revisions())
        assert len(revisions) >= 1, "At least one migration revision must be present"

        head_revision = script.get_current_head()
        assert head_revision == "daede4011b68"


    def test_schema_metadata_tables_completeness(self):
        """Validates that Base.metadata contains all 14 core entity and association tables."""
        table_names = set(Base.metadata.tables.keys())
        expected_tables = {
            "organizations",
            "teams",
            "users",
            "projects",
            "project_users",
            "documents",
            "document_chunks",
            "meetings",
            "tasks",
            "chat_sessions",
            "chat_messages",
            "activity_logs",
            "kg_entities",
            "kg_relationships",
        }

        missing_tables = expected_tables - table_names
        assert not missing_tables, f"Missing tables in Base.metadata: {missing_tables}"

    def test_table_columns_and_mixins(self):
        """Validates that core tables have required UUIDs, timestamps, and soft delete mixins."""
        # 1. Check organizations table
        org_table = Base.metadata.tables["organizations"]
        assert "id" in org_table.c
        assert "name" in org_table.c
        assert "domain" in org_table.c
        assert "created_at" in org_table.c
        assert "updated_at" in org_table.c
        assert "is_deleted" in org_table.c

        # 2. Check users table
        user_table = Base.metadata.tables["users"]
        assert "id" in user_table.c
        assert "organization_id" in user_table.c
        assert "email" in user_table.c
        assert "hashed_password" in user_table.c
        assert "role" in user_table.c
        assert "created_at" in user_table.c
        assert "is_deleted" in user_table.c

        # 3. Check document_chunks table (pgvector embedding)
        chunk_table = Base.metadata.tables["document_chunks"]
        assert "id" in chunk_table.c
        assert "document_id" in chunk_table.c
        assert "chunk_index" in chunk_table.c
        assert "content" in chunk_table.c
        assert "embedding" in chunk_table.c
        assert "metadata_json" in chunk_table.c

    def test_initial_schema_migration_functions(self):
        """Validates that initial migration defines callable upgrade and downgrade functions."""
        assert revision == "daede4011b68"
        assert callable(upgrade)
        assert callable(downgrade)
