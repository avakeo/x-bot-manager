# services/encryption.py
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# 合鍵を取得してFernetインスタンスを作成
SECRET_KEY = os.getenv("ENCRYPTION_KEY")
if not SECRET_KEY:
    raise ValueError("ENCRYPTION_KEY が .env に設定されていません。")

fernet = Fernet(SECRET_KEY.encode())

def encrypt_data(data: str) -> str:
    """文字列を暗号化する"""
    if not data:
        return ""
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(data: str) -> str:
    """暗号化された文字列を元に戻す"""
    if not data:
        return ""
    return fernet.decrypt(data.encode()).decode()
