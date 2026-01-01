import tweepy
from services.encryption import decrypt_data
import os


def send_hello_world(account):
    # 1. 保存された情報を復号
    api_key = decrypt_data(account.api_key)
    api_secret = decrypt_data(account.api_secret)
    access_token = decrypt_data(account.access_token)
    access_secret = decrypt_data(account.access_token_secret)

    # 2. X API (v2) クライアントの初期化
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )

    # 3. 投稿実行
    response = client.create_tweet(text="Hello World! from my Python Bot")
    return response


def send_tweet_with_media(account, text, image_names=None):
    """複数画像対応のツイート投稿関数（最大4枚、本文なし投稿も可能）"""
    import logging

    logger = logging.getLogger(__name__)

    # 復号処理
    auth_info = {
        "ck": decrypt_data(account.api_key),
        "cs": decrypt_data(account.api_secret),
        "at": decrypt_data(account.access_token),
        "as": decrypt_data(account.access_token_secret),
    }

    # v1.1 API（画像アップロード用）
    auth_v1 = tweepy.OAuth1UserHandler(
        auth_info["ck"], auth_info["cs"], auth_info["at"], auth_info["as"]
    )
    api_v1 = tweepy.API(auth_v1)

    # v2 API（ツイート投稿用）
    client_v2 = tweepy.Client(
        consumer_key=auth_info["ck"],
        consumer_secret=auth_info["cs"],
        access_token=auth_info["at"],
        access_token_secret=auth_info["as"],
    )

    # 画像アップロード処理
    media_ids = []
    if image_names:
        for img_name in image_names[:4]:  # 最大4枚まで
            file_path = f"static/uploads/{account.id}/{img_name}"

            if not os.path.exists(file_path):
                logger.warning(f"画像が見つかりません: {file_path}")
                continue

            try:
                media = api_v1.media_upload(filename=file_path)
                media_ids.append(media.media_id)
                logger.info(f"画像アップロード成功: {img_name}")
            except Exception as e:
                logger.error(f"画像アップロード失敗 ({img_name}): {e}")
                continue

    # テキストまたは画像のどちらかが必須
    if not text and not media_ids:
        raise ValueError(
            "テキストまたは画像が必要です（画像ファイルが見つからないか、アップロードに失敗しました）"
        )

    # 投稿実行（本文が空でも、media_idsがあれば投稿可能）
    try:
        return client_v2.create_tweet(
            text=text if text else None, media_ids=media_ids if media_ids else None
        )
    except Exception as e:
        logger.error(f"ツイート投稿失敗: {e}")
        raise
