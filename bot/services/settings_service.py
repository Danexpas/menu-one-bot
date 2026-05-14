import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.settings import Setting

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
    "about_text": "🏪 <b>Про нас</b>\n\nМи — сучасний магазин, який пропонує найкращі товари за найкращими цінами.\n\nЗв'яжіться з нами для отримання додаткової інформації!",
    "welcome_text": "Ласкаво просимо! 👋\n\nОберіть, що вас цікавить:",
    "welcome_banner": "",
    "contacts_phone": "+380 XX XXX XX XX",
    "contacts_instagram": "@your_instagram",
    "contacts_telegram": "@your_telegram",
    "contacts_address": "м. Київ, вул. Хрещатик, 1",
    "contacts_schedule": "Пн-Пт: 9:00 — 18:00\nСб-Нд: 10:00 — 16:00",
    "admin_password": "admin123",
    "shop_name": "🏪 Мій Магазин",
    "order_info": "Для оформлення замовлення зв'яжіться з нами:",
}


class SettingsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str) -> str | None:
        result = await self.session.execute(
            select(Setting).where(Setting.key == key)
        )
        setting = result.scalar_one_or_none()
        if setting is None:
            return DEFAULT_SETTINGS.get(key)
        return setting.value

    async def set(self, key: str, value: str) -> Setting:
        result = await self.session.execute(
            select(Setting).where(Setting.key == key)
        )
        setting = result.scalar_one_or_none()
        if setting is None:
            setting = Setting(key=key, value=value)
            self.session.add(setting)
        else:
            setting.value = value
        await self.session.commit()
        await self.session.refresh(setting)
        return setting

    async def get_all(self) -> dict[str, str]:
        result = await self.session.execute(select(Setting))
        settings_dict = {s.key: s.value for s in result.scalars().all()}
        merged = {**DEFAULT_SETTINGS, **settings_dict}
        return merged

    async def init_defaults(self) -> None:
        for key, value in DEFAULT_SETTINGS.items():
            result = await self.session.execute(
                select(Setting).where(Setting.key == key)
            )
            if result.scalar_one_or_none() is None:
                self.session.add(Setting(key=key, value=value))
        await self.session.commit()
        logger.info("Default settings initialized")
