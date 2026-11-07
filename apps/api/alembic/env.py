"""Migration entry point uses server DATABASE_URL, never checked-in credentials."""

import os
from alembic import context
from app.core.database import engine_for
from app.data.models import Base


# Purpose: Apply directory schema changes to the configured store. Inputs: migration context; outputs: transactional migrations.
def run_migrations():
    engine = engine_for(os.environ["DATABASE_URL"])
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=Base.metadata, compare_type=True
        )
        with context.begin_transaction():
            context.run_migrations()


run_migrations()
