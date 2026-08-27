from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import scoped_session, sessionmaker

from models.base import Base

engine = None
SessionLocal = None


def init_db(app):
    global engine, SessionLocal

    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if uri.startswith("sqlite:///"):
        engine = create_engine(uri, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(uri)

    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    Base.metadata.create_all(bind=engine)
    _run_sqlite_migrations()


def _run_sqlite_migrations():
    """Apply lightweight schema updates for existing SQLite databases."""
    if engine is None or engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "users" not in table_names:
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    with engine.begin() as conn:
        if "email" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(100)"))
        if "firebase_uid" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN firebase_uid VARCHAR(128)"))

        # SQLite cannot add unique constraints with ALTER TABLE, so use indexes.
        existing_indexes = {idx["name"] for idx in inspector.get_indexes("users")}
        if "ix_users_email_unique" not in existing_indexes:
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email_unique "
                    "ON users (email)"
                )
            )
        if "ix_users_firebase_uid_unique" not in existing_indexes:
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_firebase_uid_unique "
                    "ON users (firebase_uid)"
                )
            )

    if "dataset" in table_names:
        dataset_columns = {col["name"] for col in inspector.get_columns("dataset")}
        with engine.begin() as conn:
            if "subject" not in dataset_columns:
                conn.execute(text("ALTER TABLE dataset ADD COLUMN subject VARCHAR(120)"))
            if "topic" not in dataset_columns:
                conn.execute(text("ALTER TABLE dataset ADD COLUMN topic VARCHAR(120)"))
            if "source" not in dataset_columns:
                conn.execute(text("ALTER TABLE dataset ADD COLUMN source VARCHAR(80)"))

        # refresh inspector after schema changes
        inspector = inspect(engine)
        dataset_indexes = {idx["name"] for idx in inspector.get_indexes("dataset")}
        with engine.begin() as conn:
            if "ix_dataset_subject" not in dataset_indexes:
                conn.execute(
                    text("CREATE INDEX IF NOT EXISTS ix_dataset_subject ON dataset (subject)")
                )
            if "ix_dataset_topic" not in dataset_indexes:
                conn.execute(
                    text("CREATE INDEX IF NOT EXISTS ix_dataset_topic ON dataset (topic)")
                )
            if "ix_dataset_source" not in dataset_indexes:
                conn.execute(
                    text("CREATE INDEX IF NOT EXISTS ix_dataset_source ON dataset (source)")
                )

    if "submissions" in table_names:
        submission_columns = {col["name"] for col in inspector.get_columns("submissions")}
        with engine.begin() as conn:
            if "language" not in submission_columns:
                conn.execute(
                    text("ALTER TABLE submissions ADD COLUMN language VARCHAR(30) DEFAULT 'python'")
                )


def get_db_session():
    if SessionLocal is None:
        raise RuntimeError("Database not initialized")
    return SessionLocal()
