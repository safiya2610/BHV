import sqlite3
from contextlib import contextmanager

DB_NAME = "users.db"


def get_db():
    """
    FastAPI dependency.
    Provides a SQLite connection per request and closes it safely.
    """
    db = sqlite3.connect(
        DB_NAME,
        check_same_thread=False,
    )
    db.row_factory = sqlite3.Row

    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Safe to call multiple times.
    """
    db = sqlite3.connect(DB_NAME)
    # Enforce foreign keys for future constraints
    db.execute("PRAGMA foreign_keys = ON;")
    cur = db.cursor()

    # Detect and migrate if 'users.name' has an unintended UNIQUE constraint in existing DBs
    row = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
    if row and row[0] and "name TEXT UNIQUE" in row[0]:
        # Rebuild users table without UNIQUE on name, preserving data
        cur.executescript(
            """
            PRAGMA foreign_keys=off;
            CREATE TABLE IF NOT EXISTS users_mig (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT UNIQUE NOT NULL,
                password TEXT,
                is_private INTEGER DEFAULT 0
            );
            INSERT OR IGNORE INTO users_mig (id, name, email, password, is_private)
                SELECT id, name, email, password, is_private FROM users;
            DROP TABLE users;
            ALTER TABLE users_mig RENAME TO users;
            PRAGMA foreign_keys=on;
            """
        )

    # -------------------------
    # USERS TABLE
    # -------------------------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE NOT NULL,
            password TEXT,
            is_private INTEGER DEFAULT 0
        )
        """
    )

    # Add helpful indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")

    # -------------------------
    # IMAGES TABLE
    # -------------------------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            filename TEXT NOT NULL,
            metadata TEXT,
            visibility TEXT DEFAULT 'private',
            narrative TEXT
        )
        """
    )

    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_images_user_name ON images(user_name);"
    )

    # -------------------------
    # FRIENDS TABLE
    # -------------------------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
        """
    )

    db.commit()
    db.close()
