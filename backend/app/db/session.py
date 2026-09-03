from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# SQLite needs check_same_thread=False; Postgres does not.
# For Neon (serverless Postgres), we use NullPool to avoid keeping connections
# open between requests — Neon's serverless architecture works best this way.
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
is_neon = "neon.tech" in settings.DATABASE_URL or "neon.fl" in settings.DATABASE_URL

if is_sqlite:
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
else:
    # Postgres / Neon: use NullPool so connections are not held open between
    # requests. This is the recommended approach for serverless/PaaS Postgres.
    from sqlalchemy.pool import NullPool
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
