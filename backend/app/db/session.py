from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# SQLite needs check_same_thread=False; Postgres does not.
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if is_sqlite:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )
else:
    # Postgres on a persistent Render service: use a real connection pool so
    # every request doesn't pay the cost of a fresh TCP+SSL+auth handshake to
    # Neon on every call. NullPool is only appropriate for true serverless
    # functions that die after each invocation.
    #
    # pool_size=5        — keep up to 5 idle connections ready
    # max_overflow=10    — allow up to 10 extra connections under burst load
    # pool_timeout=30    — raise after 30 s waiting for a connection (not silent hang)
    # pool_recycle=1800  — recycle connections after 30 min to avoid stale TCP issues
    # pool_pre_ping=True — check connection health before handing it out
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
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
