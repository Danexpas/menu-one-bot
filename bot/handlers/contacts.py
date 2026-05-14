import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.main_kb import get_main_menu_keyboard
from bot.services.settings_service import SettingsService

logger = logging.getLogger(__name__)
router = Router(name="contacts")


@router.callback_query(F.data == "contacts")
async def show_contacts(callback: CallbackQuery, session: AsyncSession) -> None:
    service = SettingsService(session)
    shop_name = await service.get("shop_name") or "Магазин"
    phone = await service.get("contacts_phone") or "Не вказано"
    instagram = await service.get("contacts_instagram") or "Не вказано"
    telegram = await service.get("contacts_telegram") or "Не вказано"
    address = await service.get("contacts_address") or "Не вказано"
    schedule = await service.get("contacts_schedule") or "Не вказано"

    text = (
        f"<b>{shop_name}</b>\n\n"
        f"📞 <b>Контакти</b>\n\n"
        f"{'━' * 20}\n\n"
        f"📱 <b>Телефон:</b>\n{phone}\n\n"
        f"📸 <b>Instagram:</b>\n{instagram}\n\n"
        f"✈️ <b>Telegram:</b>\n{telegram}\n\n"
        f"📍 <b>Адреса:</b>\n{address}\n\n"
        f"🕐 <b>Графік роботи:</b>\n{schedule}\n\n"
        f"{'━' * 20}"
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()
