from cryptography.fernet import Fernet
import os
import base64
from dotenv import load_dotenv

load_dotenv()


ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")



# Ensure key is bytes
if isinstance(ENCRYPTION_KEY, str):
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()

try:
    cipher_suite = Fernet(ENCRYPTION_KEY)
    print("✅ Encryption module initialized successfully")
except ValueError as e:
    print(f"❌ Invalid encryption key: {e}")

    # Generate a temporary key to prevent crash
    ENCRYPTION_KEY = Fernet.generate_key()
    cipher_suite = Fernet(ENCRYPTION_KEY)
    print("🔑 Using temporary encryption key for this session")

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data like contact information"""
    if not data:
        return data
    try:
        encrypted_data = cipher_suite.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return data  # Return original data if encryption fails

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    if not encrypted_data:
        return encrypted_data
    try:
        decoded_data = base64.b64decode(encrypted_data.encode())
        decrypted_data = cipher_suite.decrypt(decoded_data)
        return decrypted_data.decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return encrypted_data  # Return as-is if decryption fails