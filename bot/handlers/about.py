import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.main_kb import get_main_menu_keyboard
from bot.services.settings_service import SettingsService

logger = logging.getLogger(__name__)
router = Router(name="about")


@router.callback_query(F.data == "about")
async def show_about(callback: CallbackQuery, session: AsyncSession) -> None:
    service = SettingsService(session)
    about_text = await service.get("about_text") or "ℹ️ Інформація про нас"
    shop_name = await service.get("shop_name") or "Магазин"

    text = f"<b>{shop_name}</b>\n\n{about_text}"

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()
