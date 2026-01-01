FROM python:3.13-slim

# タイムゾーンをAsia/Tokyoに設定
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 作業ディレクトリを設定
WORKDIR /app

# pyproject.tomlをコピーして依存関係をインストール
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# アプリケーションのコードをコピー
COPY . .

# static/uploadsディレクトリを作成
RUN mkdir -p static/uploads

# ポート8000を公開
EXPOSE 8000

# uvicornでFastAPIアプリを起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
