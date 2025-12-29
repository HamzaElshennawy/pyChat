import socket
import json
import base64

# Configuration
PORT = 5555
HEADER_LENGTH = 10
FORMAT = "utf-8"


# Basic "Encryption" utilizing Base64 and a simple rotation.
def encrypt_message(message):
    """
    Simple obfuscation to avoid plain text transmission.
    Encodes to Base64 and reverses the string.
    """
    try:
        encoded_bytes = base64.b64encode(message.encode(FORMAT))
        encoded_str = encoded_bytes.decode(FORMAT)
        # Simple manipulation: reverse the string
        encrypted_str = encoded_str[::-1]
        return encrypted_str
    except Exception as e:
        print(f"Encryption error: {e}")
        return message


def decrypt_message(encrypted_message):
    """
    Reverses the obfuscation.
    """
    try:
        # Reverse back
        reversed_str = encrypted_message[::-1]
        decoded_bytes = base64.b64decode(reversed_str)
        return decoded_bytes.decode(FORMAT)
    except Exception as e:
        print(f"Decryption error: {e}")
        return encrypted_message


def send_message(sock, message_dict):
    """
    Sends a JSON-serialized message with a fixed-length header.
    Dict structure: {'type': 'MSG'|'LOGIN', 'from': 'user', 'to': 'all'|'u2', 'content': 'text'}
    """
    try:
        # 1. Serialize to JSON
        json_data = json.dumps(message_dict)

        # 2. Encrypt the content part if it exists, or encrypt the whole JSON?
        # Let's encrypt the whole JSON string to hide metadata too.
        encrypted_data = encrypt_message(json_data)

        # 3. Prepare Header (Fixed 10 bytes)
        # Only allow 10 bytes for size.
        message_length = len(encrypted_data)
        header = f"{message_length:<{HEADER_LENGTH}}"

        # 4. Send
        sock.send(header.encode(FORMAT))
        sock.send(encrypted_data.encode(FORMAT))
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False


def receive_message(sock):
    """
    Receives a message from the socket.
    Returns the deserialized dictionary or None if connection closed.
    """
    try:
        # 1. Read Header
        header = sock.recv(HEADER_LENGTH)
        if not header:
            return None

        message_length = int(header.decode(FORMAT).strip())

        # Ensure we read the full message
        data = b""
        while len(data) < message_length:
            packet = sock.recv(message_length - len(data))
            if not packet:
                return None
            data += packet

        encrypted_data = data.decode(FORMAT)

        # 3. Decrypt
        decrypted_json = decrypt_message(encrypted_data)

        # 4. Deserialize
        return json.loads(decrypted_json)
    except Exception as e:
        # print(f"Error receiving message: {e}") # specific errors handled by caller
        return None
