import socket
import threading
import signal
import sys
from database import DatabaseManager
from protocol import PORT, send_message, receive_message


class ChatServer:
    def __init__(self, host="0.0.0.0", port=PORT):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen()

        self.clients = {}  # Maps username -> socket
        self.sockets = {}  # Maps socket -> username
        self.db = DatabaseManager()
        self.running = True

        print(f"[STARTING] Server listens on {host}:{port}")

    def broadcast(self, message_dict, exclude_user=None):
        """Send a message to all connected clients."""
        for user, sock in self.clients.items():
            if user != exclude_user:
                send_message(sock, message_dict)

    def handle_client(self, client_socket, address):
        """Thread function to handle a single client connection."""
        print(f"[NEW CONNECTION] {address} connected.")
        username = None

        try:
            # First message should be LOGIN
            first_msg = receive_message(client_socket)
            if first_msg and first_msg.get("type") == "LOGIN":
                username = first_msg.get("content")

                # Check if username taken
                if username in self.clients:
                    send_message(
                        client_socket, {"type": "ERROR", "content": "Username taken"}
                    )
                    client_socket.close()
                    return

                # Register user
                self.clients[username] = client_socket
                self.sockets[client_socket] = username
                self.db.add_user(username)

                print(f"[LOGIN] User: {username}")

                # Send welcome & History
                send_message(
                    client_socket, {"type": "INFO", "content": f"Welcome {username}!"}
                )

                # Send User List to everyone
                user_list = list(self.clients.keys())
                self.broadcast({"type": "USER_LIST", "content": user_list})
                # Send User List to self (broadcast does it, but just in case)

                # Retrieve and send public history
                history = self.db.get_public_history()
                for sender, content, timestamp in history:
                    send_message(
                        client_socket,
                        {
                            "type": "MSG",
                            "from": sender,
                            "to": "all",
                            "content": content,
                            "timestamp": timestamp,
                        },
                    )
            else:
                print(f"[ERROR] {address} did not send LOGIN.")
                client_socket.close()
                return

            # Main Loop
            while self.running:
                msg = receive_message(client_socket)
                if msg is None:
                    break  # Connection closed

                msg_type = msg.get("type")
                content = msg.get("content")
                recipient = msg.get("to")  # 'all' or specific username

                if msg_type == "MSG":
                    if recipient == "all":
                        # Broadcast
                        print(f"[{username} -> ALL]: {content}")
                        self.db.store_message(username, "all", "BROADCAST", content)
                        self.broadcast(
                            {
                                "type": "MSG",
                                "from": username,
                                "to": "all",
                                "content": content,
                            }
                        )
                    else:
                        # Private Message
                        target_sock = self.clients.get(recipient)
                        if target_sock:
                            print(f"[{username} -> {recipient}]: {content}")
                            self.db.store_message(
                                username, recipient, "PRIVATE", content
                            )
                            # Send to recipient
                            send_message(
                                target_sock,
                                {
                                    "type": "MSG",
                                    "from": username,
                                    "to": recipient,
                                    "content": content,
                                    "private": True,
                                },
                            )
                            # Send back to sender so they see it in their UI
                            send_message(
                                client_socket,
                                {
                                    "type": "MSG",
                                    "from": username,
                                    "to": recipient,
                                    "content": content,
                                    "private": True,
                                },
                            )
                        else:
                            send_message(
                                client_socket,
                                {
                                    "type": "ERROR",
                                    "content": f"User {recipient} not found.",
                                },
                            )

        except Exception as e:
            print(f"[EXCEPTION] {address}: {e}")
        finally:
            # Cleanup
            print(f"[DISCONNECT] {address} {username}")
            if username in self.clients:
                del self.clients[username]
            if client_socket in self.sockets:
                del self.sockets[client_socket]
            client_socket.close()
            # Update user lists
            self.broadcast({"type": "USER_LIST", "content": list(self.clients.keys())})

    def start(self):
        print("[SERVER CONNECTED] Waiting for connections...")
        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                thread = threading.Thread(
                    target=self.handle_client, args=(client_sock, addr)
                )
                thread.daemon = True  # Kills thread if main program exits
                thread.start()
            except OSError:
                break


if __name__ == "__main__":
    server = ChatServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Server stopping...")
        server.running = False
