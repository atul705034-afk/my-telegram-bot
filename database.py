import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id   INTEGER PRIMARY KEY,
                username  TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_user(self, user_id: int, username: str):
        self.conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        self.conn.commit()

    def get_all_users(self) -> list[int]:
        cursor = self.conn.execute("SELECT user_id FROM users")
        return [row[0] for row in cursor.fetchall()]

    def count_users(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]


# Single shared instance
db = Database()
