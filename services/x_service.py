import logging
import os

import tweepy

from services.encryption import decrypt_data


MAX_MEDIA_COUNT = 4
UPLOADS_DIR = os.path.join("static", "uploads")


def send_hello_world(account):
    client = _create_v2_client(account)
    return client.create_tweet(text="Hello World! from my Python Bot")


def send_tweet_with_media(account, text, image_names=None):
    """複数画像対応のツイート投稿関数（最大4枚、本文なし投稿も可能）"""
    logger = logging.getLogger(__name__)
    api_v1 = _create_v1_api(account)
    client_v2 = _create_v2_client(account)

    media_ids = _upload_media(account, api_v1, image_names, logger)

    if not text and not media_ids:
        raise ValueError(
            "テキストまたは画像が必要です（画像ファイルが見つからないか、アップロードに失敗しました）"
        )

    try:
        return client_v2.create_tweet(
            text=text if text else None, media_ids=media_ids if media_ids else None
        )
    except Exception as e:
        logger.error(f"ツイート投稿失敗: {e}")
        raise


def _decrypt_auth_info(account):
    return {
        "ck": decrypt_data(account.api_key),
        "cs": decrypt_data(account.api_secret),
        "at": decrypt_data(account.access_token),
        "as": decrypt_data(account.access_token_secret),
    }


def _create_v1_api(account):
    auth_info = _decrypt_auth_info(account)
    auth_v1 = tweepy.OAuth1UserHandler(
        auth_info["ck"], auth_info["cs"], auth_info["at"], auth_info["as"]
    )
    return tweepy.API(auth_v1)


def _create_v2_client(account):
    auth_info = _decrypt_auth_info(account)
    return tweepy.Client(
        consumer_key=auth_info["ck"],
        consumer_secret=auth_info["cs"],
        access_token=auth_info["at"],
        access_token_secret=auth_info["as"],
    )


def _upload_media(account, api_v1, image_names, logger):
    media_ids = []
    if not image_names:
        return media_ids

    for img_name in image_names[:MAX_MEDIA_COUNT]:
        file_path = os.path.join(UPLOADS_DIR, str(account.id), img_name)

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

    return media_ids
