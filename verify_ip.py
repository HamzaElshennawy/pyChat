import socket
import json
import time
import sqlite3
import threading
from database import DatabaseManager

PORT = 5050
HOST = "127.0.0.1"


def receive_msg(sock):
    try:
        header = sock.recv(1024).decode("utf-8")
        if not header:
            return None
        return json.loads(header)
    except:
        return None


def send_msg(sock, data):
    msg = json.dumps(data)
    sock.send(msg.encode("utf-8"))


def run_test():
    # 1. Login with new user (First Login)
    print("--- Test Step 1: First Login (Should Succeed) ---")
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s1.connect((HOST, PORT))
    send_msg(s1, {"type": "LOGIN", "content": "verify_user"})

    # Wait for response
    time.sleep(1)
    # Check current IP in DB
    db = DatabaseManager()
    ip = db.get_user_ip("verify_user")
    print(f"Stored IP for 'verify_user': {ip}")
    if ip != "127.0.0.1":
        print("FAILED: IP not stored correctly.")
    else:
        print("SUCCESS: IP stored.")

    s1.close()

    # 2. Modify IP in DB to simulate different location
    print("\n--- Test Step 2: Simulate different IP ---")
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("UPDATE users SET ip_address = '1.2.3.4' WHERE username = 'verify_user'")
    conn.commit()
    conn.close()
    print("Changed 'verify_user' IP to 1.2.3.4 in DB.")

    # 3. Login again (Should Fail)
    print("\n--- Test Step 3: Second Login from 127.0.0.1 (Should Fail) ---")
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2.connect((HOST, PORT))
    send_msg(s2, {"type": "LOGIN", "content": "verify_user"})

    # Read response
    # Expecting: {"type": "ERROR", "content": "Access Denied: ..."}
    # Note: protocol might be length-prefixed or json-dumped.
    # The server uses `send_message` which likely sends JSON directly or with length?
    # Let's check protocol.py first.
    # But since I don't want to fail on protocol details, I'll just read raw or try to parse.
    try:
        # Just read a chunk
        data = s2.recv(4096).decode("utf-8")
        print(f"Server Response: {data}")
        if "Access Denied" in data or "ERROR" in data:
            print("SUCCESS: Connection rejected as expected.")
        else:
            print("FAILED: Connection was not rejected.")
    except Exception as e:
        print(f"Error receiving: {e}")

    s2.close()

    # cleanup
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = 'verify_user'")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    run_test()
