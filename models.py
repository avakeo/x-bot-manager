from sqlmodel import Field, SQLModel, create_engine, Session

class Account(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str

sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()