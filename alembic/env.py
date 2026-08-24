import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.append(os.getcwd())

from server.model import Base

config = context.config

config.set_main_option(
    "sqlalchemy.url",
    os.environ.get(
        "SYNC_DATABASE_URL",
        os.environ["DATABASE_URL"].replace("+asyncpg", "+psycopg"),
    ),
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


