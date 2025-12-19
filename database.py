import sqlite3
import datetime

DB_NAME = "chat_history.db"

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Users table (track last seen if needed, simple for now)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Messages table
        # msg_type: 'BROADCAST' or 'PRIVATE'
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                recipient TEXT,
                msg_type TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_user(self, username):
        try:
            self.cursor.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
            self.conn.commit()
        except Exception as e:
            print(f"DB Error add_user: {e}")

    def store_message(self, sender, recipient, msg_type, content):
        try:
            self.cursor.execute(
                "INSERT INTO messages (sender, recipient, msg_type, content) VALUES (?, ?, ?, ?)",
                (sender, recipient, msg_type, content)
            )
            self.conn.commit()
        except Exception as e:
            print(f"DB Error store_message: {e}")

    def get_public_history(self, limit=50):
        try:
            self.cursor.execute("""
                SELECT sender, content, timestamp FROM messages 
                WHERE msg_type = 'BROADCAST' 
                ORDER BY timestamp ASC
            """) # limiting is tricky with ASC, usually fetch all or subquery. Let's fetch all for simplicity in this project.
            return self.cursor.fetchall()
        except Exception as e:
            print(f"DB Error get_public_history: {e}")
            return []

    def get_private_history(self, user1, user2):
        try:
            # Fetch messages between user1 and user2
            self.cursor.execute("""
                SELECT sender, content, timestamp FROM messages 
                WHERE msg_type = 'PRIVATE' 
                AND ((sender = ? AND recipient = ?) OR (sender = ? AND recipient = ?))
                ORDER BY timestamp ASC
            """, (user1, user2, user2, user1))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"DB Error get_private_history: {e}")
            return []
            
    def close(self):
        self.conn.close()
