from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles  # 追加
from sqlmodel import Session, select, desc
from models import (
    Account,
    Tweet,
    CSVText,
    HourlySchedule,
    get_session,
    create_db_and_tables,
)  # create_db_and_tablesを追加
from services.encryption import encrypt_data
from services.x_service import send_hello_world  # 後ほど作成する関数
from datetime import datetime
from uuid import uuid4
from typing import List, Optional
import json
import os
from pathlib import Path

app = FastAPI()

# アップロードディレクトリの定義
UPLOAD_DIR = "static/uploads"

# スケジューラーの読み込み（あれば）
try:
    from services.scheduler import start_scheduler

    has_scheduler = True
except ImportError:
    has_scheduler = False


# 起動時にテーブルを作成する（DBが空の場合）
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    # スケジューラーがあれば開始
    if has_scheduler:
        start_scheduler()


# 1. アカウント一覧取得（ダッシュボード用）
@app.get("/accounts")
def list_accounts(session: Session = Depends(get_session)):
    accounts = session.exec(select(Account)).all()
    result = []

    for acc in accounts:
        result.append(
            {
                "id": acc.id,
                "name": acc.name,
            }
        )
    return result


# アカウント情報の取得
@app.get("/accounts/{account_id}")
def get_account(account_id: int, session: Session = Depends(get_session)):
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # 暗号化されたキーはそのまま返す（セキュリティのため平文に戻さない）
    return {
        "id": account.id,
        "name": account.name,
        "api_key": "****",
        "api_secret": "****",
        "access_token": "****",
        "access_token_secret": "****",
    }


# アカウント情報の更新
@app.put("/accounts/{account_id}")
def update_account(
    account_id: int, data: dict, session: Session = Depends(get_session)
):
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # 更新可能フィールド
    if "name" in data:
        account.name = data["name"]

    # APIキーが送られてきた場合のみ更新（空でない場合）
    if data.get("api_key") and data["api_key"] != "****":
        account.api_key = encrypt_data(data["api_key"])
    if data.get("api_secret") and data["api_secret"] != "****":
        account.api_secret = encrypt_data(data["api_secret"])
    if data.get("access_token") and data["access_token"] != "****":
        account.access_token = encrypt_data(data["access_token"])
    if data.get("access_token_secret") and data["access_token_secret"] != "****":
        account.access_token_secret = encrypt_data(data["access_token_secret"])

    session.add(account)
    session.commit()
    return {"status": "success"}


# 3. テスト投稿実行
@app.post("/accounts/{account_id}/test-tweet")
def test_tweet(account_id: int, session: Session = Depends(get_session)):
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        send_hello_world(account)
        return {"status": "success", "message": "テスト投稿を送信しました"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# アカウントごとの画像一覧を取得
@app.get("/accounts/{account_id}/images")
def list_images(account_id: int):
    path = f"{UPLOAD_DIR}/{account_id}"
    if not os.path.exists(path):
        return {"images": []}

    return {"images": os.listdir(path)}


# 画像をアップロード
@app.post("/accounts/{account_id}/upload")
async def upload_image(account_id: int, file: UploadFile = File(...)):
    os.makedirs(f"{UPLOAD_DIR}/{account_id}", exist_ok=True)
    file_path = f"{UPLOAD_DIR}/{account_id}/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {"filename": file.filename, "status": "success"}


# 画像を削除
@app.delete("/accounts/{account_id}/images/{image_name}")
def delete_image(account_id: int, image_name: str):
    file_path = f"{UPLOAD_DIR}/{account_id}/{image_name}"
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Image not found")


# CSVテキストを保存
@app.post("/accounts/{account_id}/csv-texts")
def save_csv_texts(
    account_id: int, data: dict, session: Session = Depends(get_session)
):
    texts = data.get("texts", [])

    csv_text = session.exec(
        select(CSVText).where(CSVText.account_id == account_id)
    ).first()

    if csv_text:
        csv_text.texts = json.dumps(texts)
        csv_text.updated_at = datetime.now()
    else:
        csv_text = CSVText(account_id=account_id, texts=json.dumps(texts))

    session.add(csv_text)
    session.commit()
    return {"status": "success"}


# CSVテキストを取得
@app.get("/accounts/{account_id}/csv-texts")
def get_csv_texts(account_id: int, session: Session = Depends(get_session)):
    csv_text = session.exec(
        select(CSVText).where(CSVText.account_id == account_id)
    ).first()

    if not csv_text:
        return {"texts": []}

    return {"texts": json.loads(csv_text.texts)}


# ===== 時間単位スケジュール設定のCRUD =====


# 特定のアカウントのスケジュール設定一覧を取得
@app.get("/accounts/{account_id}/hourly-schedules")
def get_hourly_schedules(account_id: int, session: Session = Depends(get_session)):
    schedules = session.exec(
        select(HourlySchedule).where(HourlySchedule.account_id == account_id)
    ).all()
    return {"schedules": schedules}


# スケジュール設定を新規作成
@app.post("/accounts/{account_id}/hourly-schedules")
def create_hourly_schedule(
    account_id: int, data: dict, session: Session = Depends(get_session)
):
    schedule = HourlySchedule(
        account_id=account_id,
        name=data.get("name"),
        hours=json.dumps(data.get("hours", [])),
        start_time=data.get("start_time"),
        is_active=data.get("is_active", True),
    )
    session.add(schedule)
    session.commit()
    return {"status": "success", "id": schedule.id}


# スケジュール設定を更新
@app.put("/accounts/{account_id}/hourly-schedules/{schedule_id}")
def update_hourly_schedule(
    account_id: int,
    schedule_id: int,
    data: dict,
    session: Session = Depends(get_session),
):
    schedule = session.get(HourlySchedule, schedule_id)
    if not schedule or schedule.account_id != account_id:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if "name" in data:
        schedule.name = data["name"]
    if "hours" in data:
        schedule.hours = json.dumps(data["hours"])
    if "start_time" in data:
        schedule.start_time = data["start_time"]
    if "is_active" in data:
        schedule.is_active = data["is_active"]

    schedule.updated_at = datetime.now()
    session.add(schedule)
    session.commit()
    return {"status": "success"}


# スケジュール設定を削除
@app.delete("/accounts/{account_id}/hourly-schedules/{schedule_id}")
def delete_hourly_schedule(
    account_id: int, schedule_id: int, session: Session = Depends(get_session)
):
    schedule = session.get(HourlySchedule, schedule_id)
    if not schedule or schedule.account_id != account_id:
        raise HTTPException(status_code=404, detail="Schedule not found")

    session.delete(schedule)
    session.commit()
    return {"status": "success"}


# 静的ファイルの配信設定
app.mount("/uploads", StaticFiles(directory="static/uploads"), name="uploads")
app.mount("/", StaticFiles(directory="static", html=True), name="static")
