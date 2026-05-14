import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/bot.db")
    MEDIA_DIR: str = os.getenv("MEDIA_DIR", "./media/products")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def media_path(self) -> Path:
        path = Path(self.MEDIA_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def validate(self) -> None:
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set. Please check your .env file.")


settings = Settings()
