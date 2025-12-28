from datetime import datetime
from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import Optional
import os

sqlite_url = os.getenv("DATABASE_URL", "sqlite:///./database.db")
engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str


# --- 投稿データ（これが "posted db" の役割を兼ねます） ---
class Tweet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int
    content: Optional[str] = Field(default="")  # テキストはオプション
    image_names: str = Field(default="")  # JSON文字列で複数の画像ファイル名を保存
    is_posted: bool = Field(default=False)  # 投稿済みかどうか
    scheduled_at: Optional[datetime] = None  # 予約日時
    posted_at: Optional[datetime] = None  # 実際の投稿日時


# --- CSVテキストデータ（アカウントごとに保存） ---
class CSVText(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(unique=True)  # アカウントごとに1レコード
    texts: str = Field(default="[]")  # JSON配列で最大100件のテキストを保存
    updated_at: datetime = Field(default_factory=datetime.now)


# --- 時間単位スケジュール設定 ---
class HourlySchedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int  # アカウントID
    name: str  # スケジュール設定の名前（例: "平日スケジュール"）
    hours: str = Field(
        default="[]"
    )  # 投稿する時間のJSON配列（例: ["09:00", "12:00", "15:00"]）
    is_active: bool = Field(default=True)  # スケジュールが有効かどうか
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
