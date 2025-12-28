# services/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select
from models import engine, Account, Tweet
from services.x_service import send_tweet_with_media
from datetime import datetime
from zoneinfo import ZoneInfo
import logging
import json

# ログの設定（動いているか確認できるようにする）
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_and_post():
    """DBをチェックして投稿するメイン処理"""
    with Session(engine) as session:
        # 日本時間（JST）で現在時刻を取得
        now = datetime.now(ZoneInfo("Asia/Tokyo"))
        # 1. 投稿待ち(is_posted=False) かつ 予定時刻(scheduled_at)が現在より前のものを取得
        statement = select(Tweet).where(
            Tweet.is_posted == False, Tweet.scheduled_at <= now
        )
        pending_tweets = session.exec(statement).all()

        for tweet in pending_tweets:
            # 2. 紐づくアカウント情報を取得
            account = session.get(Account, tweet.account_id)
            if not account:
                continue

            try:
                # image_names (JSON文字列) をリストに変換
                image_names = json.loads(tweet.image_names) if tweet.image_names else []

                content_preview = tweet.content[:20] if tweet.content else "(画像のみ)"
                logger.info(
                    f"投稿実行中: {content_preview}... (画像: {len(image_names)}枚)"
                )

                # 3. 実際にXへ投稿（複数画像対応）
                send_tweet_with_media(account, tweet.content, image_names)

                # 4. DBの状態を「投稿済み」に更新
                tweet.is_posted = True
                tweet.posted_at = now
                session.add(tweet)
                logger.info(f"投稿成功！")
            except Exception as e:
                logger.error(f"投稿失敗 (ID: {tweet.id}): {e}")

        session.commit()


def start_scheduler():
    """スケジュールの開始"""
    scheduler = BackgroundScheduler()
    # 1分ごとに check_and_post を実行
    scheduler.add_job(check_and_post, "interval", minutes=1)
    scheduler.start()
    logger.info("スケジューラーが起動しました（1分ごとにチェックします）")
