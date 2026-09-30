# app/services/conversation_log_service.py
import sqlite3
import time
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class ConversationLogService:
    def __init__(self, db_path: str = "shruti_conversations.db"):
        # Same file as the LangGraph checkpointer, different table —
        # SQLite handles multiple tables in one file fine, and this
        # keeps you down to one file to manage/gitignore.
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                route TEXT,
                created_at REAL NOT NULL
            )
        """)
        self.conn.commit()

    def log_message(self, thread_id: str, role: str, content: str, route: str = None):
        self.conn.execute(
            "INSERT INTO conversation_messages (thread_id, role, content, route, created_at) VALUES (?, ?, ?, ?, ?)",
            (thread_id, role, content, route, time.time()),
        )
        self.conn.commit()

    def list_threads(self):
        cursor = self.conn.execute("""
            SELECT thread_id, MIN(content) AS title, MIN(created_at) AS created_at
            FROM conversation_messages
            WHERE role = 'user'
            GROUP BY thread_id
            ORDER BY created_at DESC
        """)
        return [{"thread_id": r[0], "title": r[1][:50], "created_at": r[2]} for r in cursor.fetchall()]

    def get_thread_messages(self, thread_id: str):
        cursor = self.conn.execute(
            "SELECT role, content, route FROM conversation_messages WHERE thread_id = ? ORDER BY id ASC",
            (thread_id,),
        )
        return [{"role": r[0], "content": r[1], "route": r[2]} for r in cursor.fetchall()]

conversation_log = ConversationLogService()