from services.encryption import decrypt_data
from models import engine, Account
from sqlmodel import Session, select

print("🔍 暗号化キーのテスト中...")

with Session(engine) as session:
    account = session.exec(select(Account)).first()
    if not account:
        print("❌ アカウントがデータベースに登録されていません")
        exit(1)

    print(f"📝 アカウント名: {account.name}")

    try:
        api_key = decrypt_data(account.api_key)
        api_secret = decrypt_data(account.api_secret)
        access_token = decrypt_data(account.access_token)
        access_token_secret = decrypt_data(account.access_token_secret)

        print("✅ 復号成功！")
        print(f"   API Key: {api_key[:10]}... (最初の10文字)")
        print(f"   API Secret: {api_secret[:10]}...")
        print(f"   Access Token: {access_token[:10]}...")
        print(f"   Access Token Secret: {access_token_secret[:10]}...")

        # 実際にX APIにアクセスしてみる
        print("\n🚀 X APIへの接続テスト中...")
        from services.x_service import send_hello_world

        try:
            response = send_hello_world(account)
            print("✅ X API 接続成功！テストツイートを投稿しました")
            print(f"   Response: {response}")
        except Exception as api_error:
            print(f"❌ X API 接続失敗: {api_error}")
            import traceback

            print(traceback.format_exc())
            print("\n考えられる原因:")
            print("  - API キーまたはトークンが間違っている")
            print(
                "  - X Developer Portal でアプリの権限が Read and Write になっていない"
            )
            print("  - アプリが無効化されている")

    except Exception as e:
        print(f"❌ 復号失敗: {e}")
        print("\n原因:")
        print("  - .env の ENCRYPTION_KEY が間違っている")
        print("  - データベースに保存したときと異なるキーを使用している")
        print("\n解決方法:")
        print("  1. 正しい ENCRYPTION_KEY を .env に設定する")
        print("  2. または database.db を削除して、アカウントを再登録する")
