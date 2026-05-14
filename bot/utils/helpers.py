import os
import uuid
import logging
import aiofiles
from pathlib import Path
from aiogram.types import PhotoSize, Message
from bot.config import settings

logger = logging.getLogger(__name__)


async def save_photo(bot, photo: PhotoSize) -> str | None:
    try:
        media_path = settings.media_path
        file_id = photo.file_id
        ext = ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = media_path / filename

        file = await bot.get_file(file_id)
        file_path = file.file_path

        await bot.download_file(file_path, destination=str(filepath))
        logger.info(f"Photo saved: {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"Error saving photo: {e}")
        return None


def delete_photo(image_path: str | None) -> None:
    if not image_path:
        return
    try:
        path = Path(image_path)
        if path.exists():
            path.unlink()
            logger.info(f"Photo deleted: {image_path}")
    except Exception as e:
        logger.error(f"Error deleting photo: {e}")


def validate_price(value: str) -> float | None:
    try:
        cleaned = value.strip().replace(",", ".").replace(" ", "")
        price = float(cleaned)
        if price < 0:
            return None
        return round(price, 2)
    except (ValueError, TypeError):
        return None


def format_price(price: float) -> str:
    if price == int(price):
        return f"{int(price):,}".replace(",", " ") + " ₴"
    return f"{price:,.2f}".replace(",", " ") + " ₴"


def truncate_text(text: str, max_len: int = 50) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
