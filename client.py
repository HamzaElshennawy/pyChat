import socket
import threading
import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from protocol import PORT, send_message, receive_message

# Set theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class ChatFrame(ctk.CTkFrame):
    """
    A reusable frame representing a single chat conversation (Group or Private).
    """

    def __init__(self, master, partner_id, sock, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.partner_id = partner_id  # 'all' or username
        self.sock = sock

        # Layout
        self.grid_rowconfigure(1, weight=1)  # Chat area expands
        self.grid_columnconfigure(0, weight=1)

        # Header
        title = "Group Chat" if partner_id == "all" else f"Private Chat: {partner_id}"
        self.lbl_header = ctk.CTkLabel(
            self, text=title, font=("Roboto", 18, "bold"), anchor="w"
        )
        self.lbl_header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)

        # Text Area
        self.msg_box = ctk.CTkTextbox(self, state="disabled")
        self.msg_box.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Input Area
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)

        self.entry_msg = ctk.CTkEntry(
            self.input_frame, placeholder_text="Type a message..."
        )
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_msg.bind("<Return>", lambda e: self.send_message())

        self.btn_send = ctk.CTkButton(
            self.input_frame, text="Send", width=100, command=self.send_message
        )
        self.btn_send.pack(side="right")

    def add_message(self, sender, content):
        self.msg_box.configure(state="normal")
        self.msg_box.insert("end", f"[{sender}]: {content}\n")
        self.msg_box.configure(state="disabled")
        self.msg_box.see("end")

    def send_message(self):
        text = self.entry_msg.get()
        if not text:
            return

        send_message(self.sock, {"type": "MSG", "to": self.partner_id, "content": text})
        self.entry_msg.delete(0, "end")


class ChatClient(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Modern LAN Chat")
        self.geometry("900x600")

        # Network State
        self.client_socket = None
        self.username = ""
        self.connected = False
        self.running = True

        # UI State
        self.frames = {}  # partner_id -> ChatFrame
        self.current_partner = None
        self.online_users = []  # List of strings
        self.unread_counts = {}  # username -> int count

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_login_ui()

    def create_login_ui(self):
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self.login_frame, text="Join Chat", font=("Roboto", 24)).pack(
            pady=20, padx=50
        )

        self.entry_ip = ctk.CTkEntry(
            self.login_frame, placeholder_text="Server IP (127.0.0.1)"
        )
        self.entry_ip.pack(pady=10)
        self.entry_ip.insert(0, "127.0.0.1")

        self.entry_username = ctk.CTkEntry(
            self.login_frame, placeholder_text="Username"
        )
        self.entry_username.pack(pady=10)

        self.btn_connect = ctk.CTkButton(
            self.login_frame, text="Connect", command=self.connect_to_server
        )
        self.btn_connect.pack(pady=20)

    def connect_to_server(self):
        ip = self.entry_ip.get()
        user = self.entry_username.get()
        if not ip or not user:
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((ip, PORT))

            send_message(self.client_socket, {"type": "LOGIN", "content": user})

            self.username = user
            self.connected = True

            self.login_frame.destroy()
            self.create_main_ui()

            listen_thread = threading.Thread(target=self.receive_loop)
            listen_thread.daemon = True
            listen_thread.start()

        except Exception as e:
            tk.messagebox.showerror("Connection Failed", f"Could not connect: {e}")

    def create_main_ui(self):
        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(
            self.sidebar, text=f"User: {self.username}", font=("Roboto", 16, "bold")
        ).pack(pady=20)

        self.user_list_frame = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent"
        )
        self.user_list_frame.pack(fill="both", expand=True)

        # --- Main Area ---
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.get_or_create_frame("all")
        self.select_chat("all")

    def get_or_create_frame(self, partner_id):
        if partner_id not in self.frames:
            frame = ChatFrame(self.main_area, partner_id, self.client_socket)
            self.frames[partner_id] = frame
        return self.frames[partner_id]

    def select_chat(self, partner_id):
        # If switching TO a user, clear their unread count
        if partner_id in self.unread_counts:
            self.unread_counts[partner_id] = 0

        # Hide current
        if self.current_partner and self.current_partner in self.frames:
            self.frames[self.current_partner].grid_forget()

        # Show new
        self.current_partner = partner_id
        frame = self.get_or_create_frame(partner_id)
        frame.grid(row=0, column=0, sticky="nsew")

        self.render_sidebar()

    def render_sidebar(self):
        """Re-draws all sidebar buttons with current notifications."""
        for w in self.user_list_frame.winfo_children():
            w.destroy()

        # Group Chat
        btn_grp = ctk.CTkButton(
            self.user_list_frame,
            text="Group Chat",
            border_width=1,
            fg_color=(
                ["#3B8ED0", "#1F6AA5"]
                if self.current_partner == "all"
                else "transparent"
            ),
            command=lambda: self.select_chat("all"),
        )
        btn_grp.pack(pady=2, fill="x")

        # Users
        for u in self.online_users:
            if u != self.username:
                # Construct Label: "User" or "User (N)"
                count = self.unread_counts.get(u, 0)
                display_text = f"{u} ({count})" if count > 0 else u

                # Highlight if active
                is_active = u == self.current_partner
                color = ["#3B8ED0", "#1F6AA5"] if is_active else "transparent"

                # Highlight if unread and not active
                if count > 0 and not is_active:
                    color = "#C0392B"  # Red-ish for notification attention

                btn = ctk.CTkButton(
                    self.user_list_frame,
                    text=display_text,
                    border_width=1,
                    fg_color=color,
                    command=lambda u=u: self.select_chat(u),
                )
                btn.pack(pady=2, fill="x")

    def receive_loop(self):
        while self.running:
            msg = receive_message(self.client_socket)
            if msg:
                self.after(0, self.process_incoming_message, msg)
            else:
                self.after(0, self.on_disconnect)
                break

    def process_incoming_message(self, msg):
        m_type = msg.get("type")
        content = msg.get("content")
        sender = msg.get("from")
        to = msg.get("to")

        if m_type == "USER_LIST":
            self.online_users = content
            self.render_sidebar()

        elif m_type == "MSG":
            is_private = msg.get("private", False)

            if is_private:
                partner = sender if sender != self.username else to
                frame = self.get_or_create_frame(partner)
                frame.add_message(sender, content)

                # Increment Unread if not looking at this chat
                if self.current_partner != partner:
                    self.unread_counts[partner] = self.unread_counts.get(partner, 0) + 1
                    self.render_sidebar()
            else:
                # Group Chat
                frame = self.get_or_create_frame("all")
                frame.add_message(sender, content)
                # Could also add unread for Group, but requirement specified Private.

        elif m_type == "INFO":
            frame = self.get_or_create_frame("all")
            frame.add_message("SYSTEM", content)

        elif m_type == "ERROR":
            tk.messagebox.showerror("Error", content)

    def on_disconnect(self):
        tk.messagebox.showwarning("Disconnected", "Server closed connection.")
        self.destroy()


if __name__ == "__main__":
    app = ChatClient()
    app.mainloop()
