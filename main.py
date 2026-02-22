from fastapi import FastAPI, Depends, HTTPException
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

app = FastAPI()

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

        result.append(
            {
                "id": acc.id,
                "name": acc.name,
                "last_tweet": last_tweet.content if last_tweet else "なし",
                "next_scheduled": (
                    next_tweet.scheduled_at.strftime("%m/%d %H:%M")
                    if next_tweet
                    else "予定なし"
                ),
            }
        )
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
        "api_key": "****",  # マスク表示
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
        # X APIを叩く
        send_hello_world(account)
        return {"status": "success", "message": "テスト投稿を送信しました"}
    except Exception as e:
        import traceback

        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"エラー詳細: {error_detail}")
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

    return {"account_name": account.name, "tweets": tweets}


# 新しいツイートを予約（DBに保存）
@app.post("/accounts/{account_id}/tweets")
def schedule_tweet(
    account_id: int, data: dict, session: Session = Depends(get_session)
):
    content = data.get("content", "").strip()
    image_names = data.get("image_names", [])  # リストで受け取る
    scheduled_at_str = data.get("scheduled_at")

    # テキストと画像の両方が空でないか確認
    if not content and not image_names:
        raise HTTPException(
            status_code=400, detail="テキストまたは画像を選択してください"
        )

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
        scheduled_at=scheduled_at,
    )
    session.add(tweet)
    session.commit()
    return {"status": "success"}


# 一括予約ツイート（複数のツイートを一度に予約）
@app.post("/accounts/{account_id}/bulk-tweets")
def schedule_bulk_tweets(
    account_id: int, data: dict, session: Session = Depends(get_session)
):
    """
    複数のツイートを一括予約

    リクエスト形式:
    {
        "tweets": [
            {
                "content": "テキスト",
                "image_names": ["img1.jpg"],
                "scheduled_at": "2024-12-24T10:00"
            },
            ...
        ]
    }
    """
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    tweets_data = data.get("tweets", [])

    if not tweets_data:
        raise HTTPException(status_code=400, detail="ツイートが指定されていません")

    if len(tweets_data) > 100:  # 一度に100個以上は登録不可
        raise HTTPException(
            status_code=400, detail="一度に登録できるツイートは100個までです"
        )

    created_count = 0
    errors = []

    for idx, tweet_data in enumerate(tweets_data):
        try:
            content = tweet_data.get("content", "").strip()
            image_names = tweet_data.get("image_names", [])
            scheduled_at_str = tweet_data.get("scheduled_at")

            # テキストと画像の確認
            if not content and not image_names:
                errors.append(f"ツイート{idx+1}: テキストまたは画像を選択してください")
                continue

            # 日時変換
            try:
                scheduled_at = datetime.fromisoformat(scheduled_at_str)
            except (ValueError, TypeError):
                errors.append(f"ツイート{idx+1}: 無効な日時形式です")
                continue

            # ツイート作成
            tweet = Tweet(
                account_id=account_id,
                content=content,
                image_names=json.dumps(image_names),
                is_posted=False,
                scheduled_at=scheduled_at,
            )
            session.add(tweet)
            created_count += 1

        except Exception as e:
            errors.append(f"ツイート{idx+1}: {str(e)}")

    # コミット
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"DB保存エラー: {str(e)}")

    # 結果を返す
    result = {
        "status": "success" if created_count > 0 else "failed",
        "created_count": created_count,
        "total": len(tweets_data),
        "errors": errors if errors else None,
    }

    if created_count == 0:
        raise HTTPException(
            status_code=400, detail=f"ツイートの登録に失敗しました: {', '.join(errors)}"
        )

    return result


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
    os.makedirs(path, exist_ok=True)  # フォルダがなければ作成

    # ファイル名衝突を避けるためUUIDを付与
    original_name = file.filename
    name, ext = os.path.splitext(original_name)
    safe_ext = ext if ext else ""
    unique_name = f"{name}_{uuid4().hex}{safe_ext}"

    file_path = os.path.join(path, unique_name)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": unique_name}


# 予約ツイートを削除（未投稿のみ）
@app.delete("/accounts/{account_id}/tweets/{tweet_id}")
def delete_tweet(
    account_id: int, tweet_id: int, session: Session = Depends(get_session)
):
    tweet = session.get(Tweet, tweet_id)
    if not tweet or tweet.account_id != account_id:
        raise HTTPException(status_code=404, detail="Tweet not found")
    if tweet.is_posted:
        raise HTTPException(status_code=400, detail="投稿済みのツイートは削除できません")
    session.delete(tweet)
    session.commit()
    return {"status": "success"}


# 画像を削除
@app.delete("/accounts/{account_id}/images/{image_name}")
def delete_image(account_id: int, image_name: str):
    file_path = f"{UPLOAD_DIR}/{account_id}/{image_name}"
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"message": "deleted"}
    raise HTTPException(status_code=404, detail="Image not found")


# CSVテキストを保存
@app.post("/accounts/{account_id}/csv-texts")
def save_csv_texts(
    account_id: int, data: dict, session: Session = Depends(get_session)
):
    """
    CSVから読み込んだテキストをDBに保存（最大100件）
    リクエストボディ: {"texts": ["text1", "text2", ...]}
    """
    texts = data.get("texts", [])

    # 100件制限
    if len(texts) > 100:
        raise HTTPException(status_code=400, detail="最大100件までです")

    # 既存レコードを検索
    statement = select(CSVText).where(CSVText.account_id == account_id)
    existing = session.exec(statement).first()

    if existing:
        # 更新
        existing.texts = json.dumps(texts, ensure_ascii=False)
        existing.updated_at = datetime.now()
        session.add(existing)
    else:
        # 新規作成
        csv_text = CSVText(
            account_id=account_id,
            texts=json.dumps(texts, ensure_ascii=False),
            updated_at=datetime.now(),
        )
        session.add(csv_text)

    session.commit()
    return {"message": "saved", "count": len(texts)}


# CSVテキストを取得
@app.get("/accounts/{account_id}/csv-texts")
def get_csv_texts(account_id: int, session: Session = Depends(get_session)):
    """
    保存されているCSVテキストを取得
    """
    statement = select(CSVText).where(CSVText.account_id == account_id)
    csv_text = session.exec(statement).first()

    if csv_text:
        texts = json.loads(csv_text.texts)
        return {"texts": texts, "count": len(texts), "updated_at": csv_text.updated_at}

    return {"texts": [], "count": 0}


# 1件ずつ予約を登録するエンドポイント（メガ予約用）
@app.post("/accounts/{account_id}/bulk-schedule-single")
def schedule_single_tweet(
    account_id: int, data: dict, session: Session = Depends(get_session)
):
    """
    単一ツイートを予約登録するエンドポイント。
    フロントエンド側で画像ごとに順次呼び出す。
    期待するリクエストペイロード例:
    {
        "content": "任意のテキスト",
        "image_name": "abc.jpg",
        "scheduled_at": "2025-01-01T10:00"
    }
    """

    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    content = (data.get("content") or "").strip()
    image_name = data.get("image_name")
    scheduled_at_str = data.get("scheduled_at")

    if not content and not image_name:
        raise HTTPException(
            status_code=400, detail="テキストまたは画像を指定してください"
        )

    if not scheduled_at_str:
        raise HTTPException(status_code=400, detail="予約日時を指定してください")

    try:
        scheduled_at = datetime.fromisoformat(scheduled_at_str)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="無効な日時形式です")

    tweet = Tweet(
        account_id=account_id,
        content=content,
        image_names=json.dumps([image_name] if image_name else []),
        is_posted=False,
        scheduled_at=scheduled_at,
    )

    session.add(tweet)
    try:
        session.commit()
    except Exception as exc:  # pragma: no cover - DB例外ハンドリング
        session.rollback()
        raise HTTPException(status_code=500, detail=f"DB保存エラー: {exc}")

    return {"status": "success"}


# ===== 時間単位スケジュール設定のCRUD =====


# 特定のアカウントのスケジュール設定一覧を取得
@app.get("/accounts/{account_id}/hourly-schedules")
def get_hourly_schedules(account_id: int, session: Session = Depends(get_session)):
    """アカウントに紐づくスケジュール設定一覧を取得"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    schedules = session.exec(
        select(HourlySchedule).where(HourlySchedule.account_id == account_id)
    ).all()

    # JSON文字列をリストに変換して返す
    result = []
    for schedule in schedules:
        result.append(
            {
                "id": schedule.id,
                "name": schedule.name,
                "hours": json.loads(schedule.hours),
                "start_time": schedule.start_time,
                "is_active": schedule.is_active,
                "created_at": schedule.created_at,
                "updated_at": schedule.updated_at,
            }
        )

    return result


# スケジュール設定を新規作成
@app.post("/accounts/{account_id}/hourly-schedules")
def create_hourly_schedule(
    account_id: int, data: dict, session: Session = Depends(get_session)
):
    """新しいスケジュール設定を作成"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    name = data.get("name", "").strip()
    hours = data.get("hours", [])  # ["09:00", "12:00", "15:00"] の形式
    start_time = data.get("start_time", None)
    is_active = data.get("is_active", True)

    if not name:
        raise HTTPException(status_code=400, detail="スケジュール名を入力してください")

    if not hours or not isinstance(hours, list):
        raise HTTPException(status_code=400, detail="時間を指定してください")

    schedule = HourlySchedule(
        account_id=account_id,
        name=name,
        hours=json.dumps(hours),
        start_time=start_time,
        is_active=is_active,
    )

    session.add(schedule)
    session.commit()
    session.refresh(schedule)

    return {
        "status": "success",
        "id": schedule.id,
        "name": schedule.name,
        "hours": json.loads(schedule.hours),
        "start_time": schedule.start_time,
        "is_active": schedule.is_active,
    }


# スケジュール設定を更新
@app.put("/accounts/{account_id}/hourly-schedules/{schedule_id}")
def update_hourly_schedule(
    account_id: int,
    schedule_id: int,
    data: dict,
    session: Session = Depends(get_session),
):
    """スケジュール設定を更新"""
    schedule = session.get(HourlySchedule, schedule_id)
    if not schedule or schedule.account_id != account_id:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if "name" in data:
        schedule.name = data["name"].strip()

    if "hours" in data:
        if not isinstance(data["hours"], list):
            raise HTTPException(
                status_code=400, detail="時間はリスト形式で指定してください"
            )
        schedule.hours = json.dumps(data["hours"])

    if "start_time" in data:
        schedule.start_time = data["start_time"]

    if "is_active" in data:
        schedule.is_active = data["is_active"]

    schedule.updated_at = datetime.now()
    session.add(schedule)
    session.commit()

    return {
        "status": "success",
        "id": schedule.id,
        "name": schedule.name,
        "hours": json.loads(schedule.hours),
        "start_time": schedule.start_time,
        "is_active": schedule.is_active,
    }


# スケジュール設定を削除
@app.delete("/accounts/{account_id}/hourly-schedules/{schedule_id}")
def delete_hourly_schedule(
    account_id: int, schedule_id: int, session: Session = Depends(get_session)
):
    """スケジュール設定を削除"""
    schedule = session.get(HourlySchedule, schedule_id)
    if not schedule or schedule.account_id != account_id:
        raise HTTPException(status_code=404, detail="Schedule not found")

    session.delete(schedule)
    session.commit()

    return {"status": "success", "message": "スケジュール設定を削除しました"}


# 静的ファイルの配信設定
app.mount("/uploads", StaticFiles(directory="static/uploads"), name="uploads")
app.mount("/", StaticFiles(directory="static", html=True), name="static")
