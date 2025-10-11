from piccolo.engine.postgres import PostgresEngine

from app.config import DATABASE_URL

# Piccolo用のデータベースエンジン設定
DB = PostgresEngine(config={"dsn": DATABASE_URL})
