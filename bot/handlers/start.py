import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.main_kb import get_start_keyboard, get_main_menu_keyboard
from bot.services.settings_service import SettingsService
from bot.services.cart_service import CartService

logger = logging.getLogger(__name__)
router = Router(name="start")

WELCOME_TEXT = (
    "✨ <b>Ласкаво просимо!</b>\n\n"
    "Раді вітати вас у нашому магазині.\n"
    "Тут ви знайдете все, що шукаєте 🛍\n\n"
    "Натисніть кнопку нижче, щоб переглянути наш каталог."
)

MAIN_MENU_TEXT = "🏪 <b>Головне меню</b>\n\nОберіть розділ, що вас цікавить 👇"


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    cfg = SettingsService(session)
    shop_name    = await cfg.get("shop_name") or "Магазин"
    welcome_text = await cfg.get("welcome_text") or WELCOME_TEXT

    await message.answer(
        text=f"<b>{shop_name}</b>\n\n{welcome_text}",
        parse_mode="HTML",
        reply_markup=get_start_keyboard(),
    )
    logger.info(f"User {message.from_user.id} started the bot")


@router.callback_query(F.data == "open_menu")
async def open_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    cfg        = SettingsService(session)
    cart_svc   = CartService(session)
    shop_name  = await cfg.get("shop_name") or "Магазин"
    cart_count = await cart_svc.count(callback.from_user.id)

    text = f"<b>{shop_name}</b>\n\n{MAIN_MENU_TEXT}"
    kb   = get_main_menu_keyboard(cart_count=cart_count)

    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=kb)
    except TelegramBadRequest:
        await callback.message.answer(text=text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()
