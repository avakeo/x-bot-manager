from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles # 追加
from sqlmodel import Session, select, desc
from models import Account, Tweet, get_session, create_db_and_tables # create_db_and_tablesを追加
from services.encryption import encrypt_data
from services.x_service import send_hello_world # 後ほど作成する関数
from datetime import datetime
from typing import List

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
def schedule_tweet(account_id: int, tweet: Tweet, session: Session = Depends(get_session)):
    tweet.account_id = account_id
    tweet.is_posted = False  # まだ投稿していない
    session.add(tweet)
    session.commit()
    return {"status": "success"}
# 4. 【重要】フロントエンドを表示するための設定
# これを一番最後に書くことで、/ にアクセスした時に static/index.html を探してくれます
app.mount("/", StaticFiles(directory="static", html=True), name="static")