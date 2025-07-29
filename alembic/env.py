import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from urllib.parse import urlparse, urlunparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models.base import Base
from app.models import user, sentence, received_audio, checked_audio
from dotenv import load_dotenv

load_dotenv()

config = context.config
fileConfig(config.config_file_name)

raw_url = os.getenv("DATABASE_URL")
parsed_url = urlparse(raw_url)

sync_url = urlunparse(
    parsed_url._replace(scheme="postgresql")
)

config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata

def run_migrations_offline():
    ...

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
