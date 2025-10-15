import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "postgresql://postgres:postgres@localhost:5430/postgres"
REDIS_URL = "redis://localhost:6379"
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
