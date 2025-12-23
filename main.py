from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
from models import Account, engine, create_db_and_tables
from services.encryption import encrypt_data

app = FastAPI()

# 起動時にテーブル作成
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/accounts")
def save_account(account: Account):
    with Session(engine) as session:
        # DBに保存する前に重要な情報を暗号化する
        account.api_key = encrypt_data(account.api_key)
        account.api_secret = encrypt_data(account.api_secret)
        account.access_token = encrypt_data(account.access_token)
        account.access_token_secret = encrypt_data(account.access_token_secret)
        
        session.add(account)
        session.commit()
        return {"status": "success", "message": f"Account '{account.name}' encrypted and saved."}

# フロントエンドを表示するための設定
app.mount("/", StaticFiles(directory="static", html=True), name="static")
