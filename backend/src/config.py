import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://srihari@localhost:5432/postgres"
    )
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    API_PORT = int(os.getenv("API_PORT", 8000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

config = Config()