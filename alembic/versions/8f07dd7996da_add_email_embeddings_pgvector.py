from alembic import op

revision = "8f07dd7996da"

down_revision = "83dcc5d88c20"
branch_labels = None
depends_on = None


def upgrade():

    op.execute(
        "CREATE EXTENSION IF NOT EXISTS vector;"
    )

    op.execute(
        """
        CREATE TABLE email_embeddings (

            id BIGSERIAL PRIMARY KEY,

            email_id INTEGER NOT NULL UNIQUE
                REFERENCES emails(id)
                ON DELETE CASCADE,

            embedding vector(384) NOT NULL,

            document TEXT NOT NULL,

            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

            created_at TIMESTAMP NOT NULL DEFAULT NOW(),

            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
        """
    )

    op.execute("""
        CREATE INDEX email_embeddings_email_idx
        ON email_embeddings(email_id);
    """)

    op.execute("""
        CREATE INDEX email_embeddings_metadata_idx
        ON email_embeddings
        USING GIN(metadata);
    """)

    op.execute("""
        CREATE INDEX email_embeddings_vector_idx
        ON email_embeddings
        USING hnsw
        (
            embedding vector_cosine_ops
        );
    """)


def downgrade():

    op.execute(
        "DROP TABLE IF EXISTS email_embeddings;"
    )