import os

from piccolo.engine.postgres import PostgresEngine

from app.config import DATABASE_URL

# Piccolo用のデータベースエンジン設定
# テスト環境ではPostgreSQL接続をスキップ
if os.getenv("TESTING"):
    DB = None  # type: ignore
else:
    DB = PostgresEngine(config={"dsn": DATABASE_URL})
