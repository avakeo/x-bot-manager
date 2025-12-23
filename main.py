from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles # 追加
from sqlmodel import Session, select, desc
from models import Account, Tweet, get_session, create_db_and_tables # create_db_and_tablesを追加
from services.encryption import encrypt_data
from services.x_service import send_hello_world # 後ほど作成する関数
from datetime import datetime
from typing import List, Optional
import json

app = FastAPI()

# 起動時にテーブルを作成する（DBが空の場合）
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# 1. アカウント一覧取得（ダッシュボード用）
@app.get("/accounts")
def list_accounts(session: Session = Depends(get_session)):
    accounts = session.exec(select(Account)).all()
    result = []
    
    for acc in accounts:
        last_tweet = session.exec(
            select(Tweet)
            .where(Tweet.account_id == acc.id, Tweet.is_posted == True)
            .order_by(desc(Tweet.posted_at))
        ).first()

        next_tweet = session.exec(
            select(Tweet)
            .where(Tweet.account_id == acc.id, Tweet.is_posted == False)
            .where(Tweet.scheduled_at > datetime.now())
            .order_by(Tweet.scheduled_at)
        ).first()

        result.append({
            "id": acc.id,
            "name": acc.name,
            "last_tweet": last_tweet.content if last_tweet else "なし",
            "next_scheduled": next_tweet.scheduled_at.strftime("%m/%d %H:%M") if next_tweet else "予定なし"
        })
    return result

# 2. アカウント登録（保存）
@app.post("/accounts")
def save_account(account: Account, session: Session = Depends(get_session)):
    # 暗号化して保存
    account.api_key = encrypt_data(account.api_key)
    account.api_secret = encrypt_data(account.api_secret)
    account.access_token = encrypt_data(account.access_token)
    account.access_token_secret = encrypt_data(account.access_token_secret)
    
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
        # X APIを叩く
        send_hello_world(account)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- main.py に追加 ---

# 特定のアカウントの投稿一覧（予約＋履歴）を取得
@app.get("/accounts/{account_id}/tweets")
def get_account_tweets(account_id: int, session: Session = Depends(get_session)):
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # 全ツイートデータ取得
    tweets = session.exec(
        select(Tweet)
        .where(Tweet.account_id == account_id)
        .order_by(desc(Tweet.scheduled_at))
    ).all()

    return {
        "account_name": account.name,
        "tweets": tweets
    }

# 新しいツイートを予約（DBに保存）
@app.post("/accounts/{account_id}/tweets")
def schedule_tweet(account_id: int, data: dict, session: Session = Depends(get_session)):
    content = data.get("content", "").strip()
    image_names = data.get("image_names", [])  # リストで受け取る
    scheduled_at_str = data.get("scheduled_at")
    
    # テキストと画像の両方が空でないか確認
    if not content and not image_names:
        raise HTTPException(status_code=400, detail="テキストまたは画像を選択してください")
    
    # 日時文字列をdatetimeオブジェクトに変換
    try:
        scheduled_at = datetime.fromisoformat(scheduled_at_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="無効な日時形式です")
    
    tweet = Tweet(
        account_id=account_id,
        content=content,
        image_names=json.dumps(image_names),  # JSON文字列で保存
        is_posted=False,
        scheduled_at=scheduled_at
    )
    session.add(tweet)
    session.commit()
    return {"status": "success"}
# 4. 【重要】フロントエンドを表示するための設定
# これを一番最後に書くことで、/ にアクセスした時に static/index.html を探してくれます

import os
import shutil
from fastapi import UploadFile, File

UPLOAD_DIR = "static/uploads"

# アカウントごとの画像一覧を取得
@app.get("/accounts/{account_id}/images")
def list_images(account_id: int):
    path = f"{UPLOAD_DIR}/{account_id}"
    if not os.path.exists(path):
        return []
    return os.listdir(path)

# 画像をアップロード
@app.post("/accounts/{account_id}/upload")
async def upload_image(account_id: int, file: UploadFile = File(...)):
    path = f"{UPLOAD_DIR}/{account_id}"
    os.makedirs(path, exist_ok=True) # フォルダがなければ作成
    
    file_path = os.path.join(path, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"filename": file.filename}
app.mount("/", StaticFiles(directory="static", html=True), name="static")