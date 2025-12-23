# X操作担当
import tweepy
from services.encryption import decrypt_data

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
        access_token_secret=access_secret
    )

    # 3. 投稿実行
    response = client.create_tweet(text="Hello World! from my Python Bot")
    return response