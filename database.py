import sqlite3
from pathlib import Path

DB_FILE = Path("botbuilder.db")


def connect():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            bot_type TEXT,
            bot_token TEXT,
            bot_username TEXT,
            channel TEXT,
            channel_url TEXT,
            status TEXT DEFAULT 'created'
        )
    """)

    conn.commit()
    conn.close()


def save_user(
    user_id,
    bot_type=None,
    bot_token=None,
    bot_username=None,
    channel=None,
    channel_url=None,
    status="created"
):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users
        (user_id, bot_type, bot_token, bot_username,
         channel, channel_url, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            bot_type=excluded.bot_type,
            bot_token=excluded.bot_token,
            bot_username=excluded.bot_username,
            channel=excluded.channel,
            channel_url=excluded.channel_url,
            status=excluded.status
    """, (
        user_id,
        bot_type,
        bot_token,
        bot_username,
        channel,
        channel_url,
        status
    ))

    conn.commit()
    conn.close()


def get_user(user_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            user_id,
            bot_type,
            bot_token,
            bot_username,
            channel,
            channel_url,
            status
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "user_id": row[0],
        "bot_type": row[1],
        "bot_token": row[2],
        "bot_username": row[3],
        "channel": row[4],
        "channel_url": row[5],
        "status": row[6],
    }


def update_status(user_id, status):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET status = ?
        WHERE user_id = ?
    """, (status, user_id))

    conn.commit()
    conn.close()
