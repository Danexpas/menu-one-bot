import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from bot.config import settings
from bot.database.session import create_tables
from bot.handlers import main_router
from bot.middlewares.db_middleware import DatabaseMiddleware
from bot.services.settings_service import SettingsService
from bot.database.session import async_session_factory

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    await create_tables()

    async with async_session_factory() as session:
        service = SettingsService(session)
        await service.init_defaults()

    await bot.set_my_commands(
        commands=[
            BotCommand(command="start", description="🏪 Запустити бота"),
            BotCommand(command="admin", description="🔐 Адмін-панель"),
        ],
        scope=BotCommandScopeDefault(),
    )

    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username} ({me.id})")


async def on_shutdown(bot: Bot) -> None:
    logger.info("Bot is shutting down...")
    await bot.session.close()


async def main() -> None:
    Path("data").mkdir(exist_ok=True)
    Path("media/products").mkdir(parents=True, exist_ok=True)

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())

    dp.include_router(main_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
