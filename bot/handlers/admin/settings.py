import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from bot.states.admin_states import AdminSettingsStates
from bot.keyboards.admin_kb import (
    get_admin_menu_keyboard,
    get_contacts_keyboard,
    get_settings_keyboard,
    get_back_keyboard,
)
from bot.services.settings_service import SettingsService

logger = logging.getLogger(__name__)
router = Router(name="admin_settings")


# ──── About ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_about")
async def edit_about_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    current = await service.get("about_text") or ""

    await state.set_state(AdminSettingsStates.edit_about)
    await callback.message.edit_text(
        f"ℹ️ <b>Редагувати «Про нас»</b>\n\n"
        f"Поточний текст:\n<i>{current[:300]}{'...' if len(current) > 300 else ''}</i>\n\n"
        "Введіть новий текст (підтримується HTML форматування):",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_menu"),
    )
    await callback.answer()


@router.message(AdminSettingsStates.edit_about)
async def edit_about_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    text = message.text or message.caption or ""
    service = SettingsService(session)
    await service.set("about_text", text)
    await state.clear()

    await message.answer(
        "✅ <b>Текст «Про нас» оновлено!</b>",
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard(),
    )
    logger.info("About text updated")


# ──── Contacts ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_contacts")
async def show_contacts_admin(callback: CallbackQuery, session: AsyncSession) -> None:
    service = SettingsService(session)
    phone = await service.get("contacts_phone") or "—"
    instagram = await service.get("contacts_instagram") or "—"
    telegram_contact = await service.get("contacts_telegram") or "—"
    address = await service.get("contacts_address") or "—"
    schedule = await service.get("contacts_schedule") or "—"

    text = (
        f"📞 <b>Управління контактами</b>\n\n"
        f"📱 Телефон: {phone}\n"
        f"📸 Instagram: {instagram}\n"
        f"✈️ Telegram: {telegram_contact}\n"
        f"📍 Адреса: {address}\n"
        f"🕐 Графік: {schedule}\n\n"
        "Оберіть поле для редагування:"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_contacts_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_edit_phone")
async def edit_phone_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    current = await service.get("contacts_phone") or "—"
    await state.set_state(AdminSettingsStates.edit_phone)
    await callback.message.edit_text(
        f"📱 <b>Редагувати телефон</b>\n\nПоточний: {current}\n\nВведіть новий номер телефону:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_contacts"),
    )
    await callback.answer()


@router.message(AdminSettingsStates.edit_phone)
async def edit_phone_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    await service.set("contacts_phone", message.text.strip())
    await state.clear()
    await message.answer("✅ Телефон оновлено!", reply_markup=get_contacts_keyboard())


@router.callback_query(F.data == "admin_edit_instagram")
async def edit_instagram_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    current = await service.get("contacts_instagram") or "—"
    await state.set_state(AdminSettingsStates.edit_instagram)
    await callback.message.edit_text(
        f"📸 <b>Редагувати Instagram</b>\n\nПоточний: {current}\n\nВведіть @нік або URL:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_contacts"),
    )
    await callback.answer()


@router.message(AdminSettingsStates.edit_instagram)
async def edit_instagram_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    await service.set("contacts_instagram", message.text.strip())
    await state.clear()
    await message.answer("✅ Instagram оновлено!", reply_markup=get_contacts_keyboard())


@router.callback_query(F.data == "admin_edit_telegram")
async def edit_telegram_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    current = await service.get("contacts_telegram") or "—"
    await state.set_state(AdminSettingsStates.edit_telegram)
    await callback.message.edit_text(
        f"✈️ <b>Редагувати Telegram</b>\n\nПоточний: {current}\n\nВведіть @нік або посилання:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_contacts"),
    )
    await callback.answer()


@router.message(AdminSettingsStates.edit_telegram)
async def edit_telegram_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    await service.set("contacts_telegram", message.text.strip())
    await state.clear()
    await message.answer("✅ Telegram оновлено!", reply_markup=get_contacts_keyboard())


@router.callback_query(F.data == "admin_edit_address")
async def edit_address_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    current = await service.get("contacts_address") or "—"
    await state.set_state(AdminSettingsStates.edit_address)
    await callback.message.edit_text(
        f"📍 <b>Редагувати адресу</b>\n\nПоточна: {current}\n\nВведіть нову адресу:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_contacts"),
    )
    await callback.answer()


@router.message(AdminSettingsStates.edit_address)
async def edit_address_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    await service.set("contacts_address", message.text.strip())
    await state.clear()
    await message.answer("✅ Адресу оновлено!", reply_markup=get_contacts_keyboard())


@router.callback_query(F.data == "admin_edit_schedule")
async def edit_schedule_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    current = await service.get("contacts_schedule") or "—"
    await state.set_state(AdminSettingsStates.edit_schedule)
    await callback.message.edit_text(
        f"🕐 <b>Редагувати графік роботи</b>\n\nПоточний:\n{current}\n\nВведіть новий графік:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_contacts"),
    )
    await callback.answer()


@router.message(AdminSettingsStates.edit_schedule)
async def edit_schedule_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    await service.set("contacts_schedule", message.text.strip())
    await state.clear()
    await message.answer("✅ Графік роботи оновлено!", reply_markup=get_contacts_keyboard())


# ──── General settings ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_settings")
async def show_settings(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "⚙️ <b>Загальні налаштування</b>\n\nОберіть параметр для редагування:",
        parse_mode="HTML",
        reply_markup=get_settings_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_edit_shop_name")
async def edit_shop_name_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    current = await service.get("shop_name") or "—"
    await state.set_state(AdminSettingsStates.edit_shop_name)
    await callback.message.edit_text(
        f"🏪 <b>Редагувати назву магазину</b>\n\nПоточна: {current}\n\nВведіть нову назву:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_settings"),
    )
    await callback.answer()


@router.message(AdminSettingsStates.edit_shop_name)
async def edit_shop_name_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    await service.set("shop_name", message.text.strip())
    await state.clear()
    await message.answer("✅ Назву магазину оновлено!", reply_markup=get_settings_keyboard())


@router.callback_query(F.data == "admin_edit_welcome")
async def edit_welcome_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    current = await service.get("welcome_text") or "—"
    await state.set_state(AdminSettingsStates.edit_welcome_text)
    await callback.message.edit_text(
        f"👋 <b>Редагувати текст привітання</b>\n\nПоточний:\n<i>{current[:200]}</i>\n\nВведіть новий текст:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_settings"),
    )
    await callback.answer()


@router.message(AdminSettingsStates.edit_welcome_text)
async def edit_welcome_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    await service.set("welcome_text", message.text.strip())
    await state.clear()
    await message.answer("✅ Текст привітання оновлено!", reply_markup=get_settings_keyboard())


@router.callback_query(F.data == "admin_edit_order_info")
async def edit_order_info_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    current = await service.get("order_info") or "—"
    await state.set_state(AdminSettingsStates.edit_order_info)
    await callback.message.edit_text(
        f"🛒 <b>Редагувати інформацію про замовлення</b>\n\nПоточна:\n<i>{current[:200]}</i>\n\nВведіть новий текст:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_settings"),
    )
    await callback.answer()


@router.message(AdminSettingsStates.edit_order_info)
async def edit_order_info_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    service = SettingsService(session)
    await service.set("order_info", message.text.strip())
    await state.clear()
    await message.answer("✅ Інформацію про замовлення оновлено!", reply_markup=get_settings_keyboard())


# ──── Change password ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_change_password")
async def change_password_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminSettingsStates.change_password)
    await callback.message.edit_text(
        "🔑 <b>Зміна пароля</b>\n\nВведіть новий пароль адміна:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_menu"),
    )
    await callback.answer()


@router.message(AdminSettingsStates.change_password)
async def change_password_process(message: Message, state: FSMContext) -> None:
    new_password = message.text.strip() if message.text else ""
    await message.delete()

    if len(new_password) < 4:
        await message.answer("❌ Пароль має бути не менше 4 символів. Спробуйте ще раз:")
        return

    await state.update_data(new_admin_password=new_password)
    await state.set_state(AdminSettingsStates.confirm_password)
    await message.answer(
        "🔑 <b>Підтвердження</b>\n\nВведіть новий пароль ще раз для підтвердження:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_menu"),
    )


@router.message(AdminSettingsStates.confirm_password)
async def confirm_password_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    confirm = message.text.strip() if message.text else ""
    await message.delete()

    data = await state.get_data()
    new_password = data.get("new_admin_password", "")

    if confirm != new_password:
        await message.answer("❌ Паролі не співпадають. Почніть знову: /admin")
        await state.clear()
        return

    service = SettingsService(session)
    await service.set("admin_password", new_password)
    await state.clear()

    await message.answer(
        "✅ <b>Пароль успішно змінено!</b>",
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard(),
    )
    logger.info(f"Admin password changed by user {message.from_user.id}")
