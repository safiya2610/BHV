import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")


def get_db():
    db = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON;")
    cur = db.cursor()

    # ===== USERS TABLE (with migration safety) =====
    row = cur.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"
    ).fetchone()

    if row and row[0] and "name TEXT UNIQUE" in row[0]:
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

    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);"
    )

    # ===== IMAGES TABLE =====
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

    # ===== ADMINS TABLE =====
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL
        )
        """
    )

    db.commit()
    db.close()
