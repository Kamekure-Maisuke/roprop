import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "postgresql://postgres:postgres@localhost:5430/postgres"
REDIS_URL = "redis://localhost:6379"
API_TOKEN = os.getenv("API_TOKEN", "your-secret-token-change-me")
WEB_BASIC_USERNAME = os.getenv("WEB_BASIC_USERNAME", "xxx")
WEB_BASIC_PASSWORD = os.getenv("WEB_BASIC_PASSWORD", "xxx")
