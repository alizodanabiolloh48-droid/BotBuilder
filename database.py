import os
import sqlite3
from contextlib import contextmanager
from cryptography.fernet import Fernet

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "bot_builder.db"
)

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise RuntimeError("ENCRYPTION_KEY ёфт нашуд!")

cipher = Fernet(ENCRYPTION_KEY.encode())


@contextmanager
def get_db():
    db = sqlite3.connect(
        DATABASE_PATH,
        timeout=30,
        check_same_thread=False
    )
    db.row_factory = sqlite3.Row

    try:
        yield db
        db.commit()
    finally:
        db.close()


def init_db():
    with get_db() as db:

        db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            bot_id INTEGER UNIQUE NOT NULL,
            bot_username TEXT,
            bot_name TEXT,
            token_encrypted TEXT NOT NULL,
            category TEXT,
            channel_username TEXT,
            channel_url TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_id TEXT NOT NULL,
            file_type TEXT,
            message_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        db.execute("""
        CREATE INDEX IF NOT EXISTS idx_files_name
        ON files(file_name)
        """)


def add_user(user_id):
    with get_db() as db:
        db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,)
        )


def encrypt_token(token):
    return cipher.encrypt(token.encode()).decode()


def decrypt_token(token):
    return cipher.decrypt(token.encode()).decode()


def save_bot(
    owner_id,
    bot_id,
    bot_username,
    bot_name,
    token,
    category,
    channel_username,
    channel_url
):
    encrypted = encrypt_token(token)

    with get_db() as db:
        db.execute("""
        INSERT INTO bots (
            owner_id,
            bot_id,
            bot_username,
            bot_name,
            token_encrypted,
            category,
            channel_username,
            channel_url,
            active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)

        ON CONFLICT(bot_id) DO UPDATE SET
            owner_id=excluded.owner_id,
            bot_username=excluded.bot_username,
            bot_name=excluded.bot_name,
            token_encrypted=excluded.token_encrypted,
            category=excluded.category,
            channel_username=excluded.channel_username,
            channel_url=excluded.channel_url,
            active=1
        """, (
            owner_id,
            bot_id,
            bot_username,
            bot_name,
            encrypted,
            category,
            channel_username,
            channel_url
        ))


def get_bot(bot_id):
    with get_db() as db:
        return db.execute(
            "SELECT * FROM bots WHERE bot_id=?",
            (bot_id,)
        ).fetchone()


def get_user_bots(owner_id):
    with get_db() as db:
        return db.execute("""
        SELECT *
        FROM bots
        WHERE owner_id=?
        ORDER BY id DESC
        """, (owner_id,)).fetchall()


def get_active_bots():
    with get_db() as db:
        return db.execute("""
        SELECT *
        FROM bots
        WHERE active=1
        """).fetchall()


def set_bot_active(bot_id, active):
    with get_db() as db:
        db.execute("""
        UPDATE bots
        SET active=?
        WHERE bot_id=?
        """, (1 if active else 0, bot_id))


def delete_bot(bot_id, owner_id):
    with get_db() as db:

        db.execute("""
        DELETE FROM files
        WHERE bot_id=?
        """, (bot_id,))

        db.execute("""
        DELETE FROM bots
        WHERE bot_id=?
        AND owner_id=?
        """, (bot_id, owner_id))


def add_file(
    bot_id,
    file_name,
    file_id,
    file_type,
    message_id
):
    with get_db() as db:
        db.execute("""
        INSERT INTO files (
            bot_id,
            file_name,
            file_id,
            file_type,
            message_id
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            bot_id,
            file_name,
            file_id,
            file_type,
            message_id
        ))


def search_files(bot_id, query, limit=20):
    with get_db() as db:
        return db.execute("""
        SELECT *
        FROM files
        WHERE bot_id=?
        AND file_name LIKE ?
        ORDER BY id DESC
        LIMIT ?
        """, (
            bot_id,
            f"%{query}%",
            limit
        )).fetchall()
