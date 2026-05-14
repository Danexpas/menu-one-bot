import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from bot.states.admin_states import AdminCategoryStates
from bot.keyboards.admin_kb import (
    get_admin_menu_keyboard,
    get_category_list_keyboard,
    get_category_actions_keyboard,
    get_confirm_delete_keyboard,
    get_back_keyboard,
)
from bot.services.category_service import CategoryService
from bot.services.product_service import ProductService

logger = logging.getLogger(__name__)
router = Router(name="admin_categories")

COMMON_EMOJIS = ["📦", "🍕", "🍰", "🛍", "👗", "💄", "🏠", "🎁", "🌿", "⚡"]


@router.callback_query(F.data == "admin_categories")
async def show_categories(callback: CallbackQuery, session: AsyncSession) -> None:
    service = CategoryService(session)
    categories = await service.get_all()

    count = len(categories)
    text = (
        f"📂 <b>Управління категоріями</b>\n\n"
        f"Всього категорій: <b>{count}</b>\n\n"
        "Оберіть категорію для редагування або додайте нову:"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=get_category_list_keyboard(categories)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cat_manage_"))
async def category_actions(callback: CallbackQuery, session: AsyncSession) -> None:
    category_id = int(callback.data.split("_")[-1])
    service = CategoryService(session)
    prod_service = ProductService(session)

    category = await service.get_by_id(category_id)
    if not category:
        await callback.answer("❌ Категорія не знайдена", show_alert=True)
        return

    prod_count = await prod_service.count_by_category(category_id)

    text = (
        f"📂 <b>Категорія: {category.emoji} {category.name}</b>\n\n"
        f"📦 Товарів у категорії: <b>{prod_count}</b>\n\n"
        "Оберіть дію:"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=get_category_actions_keyboard(category_id)
    )
    await callback.answer()


@router.callback_query(F.data == "admin_cat_add")
async def add_category_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminCategoryStates.waiting_name)
    await callback.message.edit_text(
        "📂 <b>Додати категорію</b>\n\n"
        "Введіть назву нової категорії:\n\n"
        "<i>Наприклад: Торти, Печиво, Тістечка</i>",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_categories"),
    )
    await callback.answer()


@router.message(AdminCategoryStates.waiting_name)
async def add_category_name(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = message.text.strip()
    if len(name) < 1 or len(name) > 100:
        await message.answer("❌ Назва повинна бути від 1 до 100 символів. Спробуйте ще раз:")
        return

    await state.update_data(category_name=name)
    await state.set_state(AdminCategoryStates.waiting_emoji)

    emojis_text = "  ".join(COMMON_EMOJIS)
    await message.answer(
        f"✅ Назва: <b>{name}</b>\n\n"
        f"Тепер введіть емодзі для категорії:\n\n"
        f"Часто використовувані:\n{emojis_text}\n\n"
        f"<i>Або натисніть /skip щоб пропустити (буде використано 📦)</i>",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_categories"),
    )


@router.message(AdminCategoryStates.waiting_emoji)
async def add_category_emoji(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if message.text and message.text.strip() == "/skip":
        emoji = "📦"
    else:
        emoji = message.text.strip() if message.text else "📦"
        if len(emoji) > 10:
            emoji = emoji[:1]

    data = await state.get_data()
    name = data.get("category_name", "")

    service = CategoryService(session)
    category = await service.create(name=name, emoji=emoji)

    await state.clear()
    categories = await service.get_all()

    await message.answer(
        f"✅ <b>Категорію створено!</b>\n\n"
        f"{emoji} <b>{name}</b>",
        parse_mode="HTML",
        reply_markup=get_category_list_keyboard(categories),
    )
    logger.info(f"Category created: {category.id} - {name}")


@router.callback_query(F.data.startswith("admin_cat_rename_"))
async def rename_category_start(callback: CallbackQuery, state: FSMContext) -> None:
    category_id = int(callback.data.split("_")[-1])
    await state.set_state(AdminCategoryStates.waiting_new_name)
    await state.update_data(edit_category_id=category_id)

    await callback.message.edit_text(
        "✏️ <b>Перейменувати категорію</b>\n\n"
        "Введіть нову назву:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_categories"),
    )
    await callback.answer()


@router.message(AdminCategoryStates.waiting_new_name)
async def rename_category_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    new_name = message.text.strip()
    if len(new_name) < 1 or len(new_name) > 100:
        await message.answer("❌ Назва повинна бути від 1 до 100 символів. Спробуйте ще раз:")
        return

    data = await state.get_data()
    category_id = data.get("edit_category_id")

    service = CategoryService(session)
    category = await service.update(category_id, name=new_name)

    await state.clear()

    if category:
        categories = await service.get_all()
        await message.answer(
            f"✅ <b>Категорію перейменовано!</b>\n\n"
            f"{category.emoji} <b>{new_name}</b>",
            parse_mode="HTML",
            reply_markup=get_category_list_keyboard(categories),
        )
        logger.info(f"Category {category_id} renamed to {new_name}")
    else:
        await message.answer(
            "❌ <b>Категорію не знайдено</b>",
            parse_mode="HTML",
            reply_markup=get_back_keyboard("admin_categories"),
        )


@router.callback_query(F.data.startswith("admin_cat_delete_"))
async def delete_category_confirm(callback: CallbackQuery, session: AsyncSession) -> None:
    category_id = int(callback.data.split("_")[-1])
    service = CategoryService(session)
    prod_service = ProductService(session)

    category = await service.get_by_id(category_id)
    if not category:
        await callback.answer("❌ Категорія не знайдена", show_alert=True)
        return

    prod_count = await prod_service.count_by_category(category_id)

    text = (
        f"🗑 <b>Видалити категорію?</b>\n\n"
        f"{category.emoji} <b>{category.name}</b>\n\n"
    )
    if prod_count > 0:
        text += f"⚠️ <b>Увага!</b> У категорії є <b>{prod_count}</b> товарів.\n"
        text += "Вони також будуть видалені!\n\n"
    text += "Ви впевнені?"

    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=get_confirm_delete_keyboard("cat", category_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_cat_"))
async def delete_category_execute(callback: CallbackQuery, session: AsyncSession) -> None:
    category_id = int(callback.data.split("_")[-1])
    service = CategoryService(session)

    category = await service.get_by_id(category_id)
    name = f"{category.emoji} {category.name}" if category else "невідома"

    success = await service.delete(category_id)

    if success:
        categories = await service.get_all()
        await callback.message.edit_text(
            f"✅ <b>Категорію видалено:</b> {name}",
            parse_mode="HTML",
            reply_markup=get_category_list_keyboard(categories),
        )
        logger.info(f"Category {category_id} deleted")
    else:
        await callback.answer("❌ Помилка видалення", show_alert=True)


@router.callback_query(F.data.startswith("cancel_delete_cat_"))
async def cancel_delete_category(callback: CallbackQuery, session: AsyncSession) -> None:
    category_id = int(callback.data.split("_")[-1])
    service = CategoryService(session)
    category = await service.get_by_id(category_id)

    if category:
        prod_service = ProductService(session)
        prod_count = await prod_service.count_by_category(category_id)
        text = (
            f"📂 <b>Категорія: {category.emoji} {category.name}</b>\n\n"
            f"📦 Товарів: <b>{prod_count}</b>\n\n"
            "Оберіть дію:"
        )
        await callback.message.edit_text(
            text, parse_mode="HTML",
            reply_markup=get_category_actions_keyboard(category_id)
        )
    await callback.answer("Скасовано")
