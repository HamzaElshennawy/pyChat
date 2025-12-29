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
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT
            )
        """
        )

        # Try to add ip_address column if it doesn't exist (migration for existing db)
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN ip_address TEXT")
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column likely already exists
            pass

        # Messages table
        # msg_type: 'BROADCAST' or 'PRIVATE'
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                recipient TEXT,
                msg_type TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        self.conn.commit()

    def add_user(self, username, ip_address):
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO users (username, ip_address) VALUES (?, ?)",
                (username, ip_address),
            )
            # Update IP if it was previously NULL (first login since feature added)
            self.cursor.execute(
                "UPDATE users SET ip_address = ? WHERE username = ? AND ip_address IS NULL",
                (ip_address, username),
            )
            self.conn.commit()
        except Exception as e:
            print(f"DB Error add_user: {e}")

    def get_user_ip(self, username):
        try:
            self.cursor.execute(
                "SELECT ip_address FROM users WHERE username = ?", (username,)
            )
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"DB Error get_user_ip: {e}")
            return None

    def store_message(self, sender, recipient, msg_type, content):
        try:
            self.cursor.execute(
                "INSERT INTO messages (sender, recipient, msg_type, content) VALUES (?, ?, ?, ?)",
                (sender, recipient, msg_type, content),
            )
            self.conn.commit()
        except Exception as e:
            print(f"DB Error store_message: {e}")

    def get_public_history(self, limit=50):
        try:
            self.cursor.execute(
                """
                SELECT sender, content, timestamp FROM messages 
                WHERE msg_type = 'BROADCAST' 
                ORDER BY timestamp ASC
            """
            )  # limiting is tricky with ASC, usually fetch all or subquery. Let's fetch all for simplicity in this project.
            return self.cursor.fetchall()
        except Exception as e:
            print(f"DB Error get_public_history: {e}")
            return []

    def get_private_history(self, user1, user2):
        try:
            # Fetch messages between user1 and user2
            self.cursor.execute(
                """
                SELECT sender, content, timestamp FROM messages 
                WHERE msg_type = 'PRIVATE' 
                AND ((sender = ? AND recipient = ?) OR (sender = ? AND recipient = ?))
                ORDER BY timestamp ASC
            """,
                (user1, user2, user2, user1),
            )
            return self.cursor.fetchall()
        except Exception as e:
            print(f"DB Error get_private_history: {e}")
            return []

    def close(self):
        self.conn.close()
