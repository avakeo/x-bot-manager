from fastapi import FastAPI, Depends
from sqlmodel import Session
from models import Account, engine, create_db_and_tables

app = FastAPI()

# 起動時にテーブル作成
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/accounts")
def save_account(account: Account):
    with Session(engine) as session:
        session.add(account)
        session.commit()
        return {"status": "success", "name": account.name}