# 💬 Modern LAN Chat Application

A robust, cross-platform, multi-threaded Chat Application built with **Python** and **CustomTkinter**.  
Designed for **Local Area Networks (LAN)**, supporting both Wired (Ethernet) and Wireless (Wi-Fi) connections without requiring Internet access.

## ✨ Features

-   **🖥 Modern UI**: Clean, dark-themed interface using `CustomTkinter`.
-   **🔒 Private Messaging**: Secure 1-on-1 chats with **Notificaton Badges** 🔴 for unread messages.
-   **👥 Group Chat**: Broadcast messaging to all connected users.
-   **💾 Persistence**: Automatic message history storage using **SQLite**.
-   **🚀 Multi-Threaded Server**: Handles multiple concurrent client connections efficiently.
-   **🛡 Basic Security**: Messages are encoded/encrypted to prevent plain-text sniffing.
-   **📶 LAN Ready**: Works perfectly over Wi-Fi or Ethernet.

## 🛠 Tech Stack

-   **Language**: Python 3.10+
-   **GUI Engine**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
-   **Networking**: Python `socket` (TCP/IP), `threading`
-   **Database**: SQLite3

## 📦 Installation

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/yourusername/lan-chat-app.git
    cd lan-chat-app
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Usage

### 1. Start the Server

Run the server on the host machine. This machine will act as the central hub.

```bash
python server.py
```

_The server listens on `0.0.0.0` (all interfaces)._

### 2. Start Clients

Run the client application on the same machine or other computers on the network.

```bash
python client.py
```

### 3. Connect

-   **Server IP**:
    -   **Same PC**: Use `127.0.0.1`
    -   **LAN**: Enter the **IPv4 Address** of the Host PC (e.g., `192.168.1.5`).
-   **Username**: Choose a unique display name.

## 📂 Project Structure

```text
├── server.py           # Multi-threaded server logic
├── client.py           # Modern GUI Client (Single-Window)
├── database.py         # SQLite database handler
├── protocol.py         # Shared networking & encryption protocols
├── requirements.txt    # Project dependencies
└── README.md           # Documentation
```

## 📸 Screenshots

_(Add screenshots of your app here)_

## 🤝 Contributing

Contributions are welcome! Please fork the repository and open a Pull Request.

## 📜 License

This project is open-source and available under the MIT License.
