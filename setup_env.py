#!/usr/bin/env python3
"""
.env ファイルに ENCRYPTION_KEY を生成して書き込むスクリプト。
既に .env がある場合は上書きしない。
"""
import os
from cryptography.fernet import Fernet

env_path = os.path.join(os.path.dirname(__file__), ".env")

if os.path.exists(env_path):
    print(f".env は既に存在します。上書きしません。\n  → {env_path}")
else:
    key = Fernet.generate_key().decode()
    with open(env_path, "w") as f:
        f.write(f'ENCRYPTION_KEY="{key}"\n')
    print(f".env を作成しました。\n  → {env_path}")
    print(f"  ENCRYPTION_KEY={key}")
