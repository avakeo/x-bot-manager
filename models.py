from datetime import datetime
from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import Optional

sqlite_url = "sqlite:///database.db"
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
    posted_at: Optional[datetime] = None     # 実際の投稿日時
