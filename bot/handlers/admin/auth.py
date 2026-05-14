import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from bot.states.admin_states import AdminAuth
from bot.keyboards.admin_kb import get_admin_menu_keyboard, get_back_keyboard
from bot.services.settings_service import SettingsService

logger = logging.getLogger(__name__)
router = Router(name="admin_auth")


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminAuth.waiting_password)
    await message.answer(
        "🔐 <b>Адмін-панель</b>\n\n"
        "Введіть пароль для входу:",
        parse_mode="HTML",
    )
    logger.info(f"Admin auth attempt by user {message.from_user.id}")


@router.message(AdminAuth.waiting_password)
async def process_admin_password(message: Message, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    stored_password = await service.get("admin_password")

    await message.delete()

    if message.text == stored_password:
        await state.clear()
        await state.update_data(is_admin=True, admin_user_id=message.from_user.id)
        await message.answer(
            "✅ <b>Авторизація успішна!</b>\n\n"
            "Ласкаво просимо до адмін-панелі 👋",
            parse_mode="HTML",
            reply_markup=get_admin_menu_keyboard(),
        )
        logger.info(f"Admin {message.from_user.id} logged in successfully")
    else:
        await state.clear()
        await message.answer(
            "❌ <b>Невірний пароль</b>\n\n"
            "Спробуйте ще раз: /admin",
            parse_mode="HTML",
        )
        logger.warning(f"Failed admin login attempt by user {message.from_user.id}")


@router.callback_query(F.data == "admin_menu")
async def show_admin_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "⚙️ <b>Адмін-панель</b>\n\n"
        "Оберіть розділ для управління:",
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_exit")
async def admin_exit(callback: CallbackQuery, session: AsyncSession) -> None:
    from bot.services.settings_service import SettingsService
    from bot.services.cart_service import CartService
    from bot.keyboards.main_kb import get_main_menu_keyboard

    cfg        = SettingsService(session)
    shop_name  = await cfg.get("shop_name") or "Магазин"
    cart_count = await CartService(session).count(callback.from_user.id)

    await callback.message.edit_text(
        f"<b>{shop_name}</b>\n\n"
        "🏪 <b>Головне меню</b>\n\n"
        "Оберіть розділ, що вас цікавить 👇",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(cart_count=cart_count),
    )
    await callback.answer("Вийшли з адмін-панелі")
    logger.info(f"Admin {callback.from_user.id} logged out")
