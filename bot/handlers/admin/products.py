import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from bot.states.admin_states import AdminProductStates
from bot.keyboards.admin_kb import (
    get_product_list_keyboard,
    get_product_actions_keyboard,
    get_product_edit_fields_keyboard,
    get_select_category_keyboard,
    get_confirm_delete_keyboard,
    get_back_keyboard,
)
from bot.services.category_service import CategoryService
from bot.services.product_service import ProductService
from bot.utils.helpers import save_photo, delete_photo, validate_price, format_price

logger = logging.getLogger(__name__)
router = Router(name="admin_products")


@router.callback_query(F.data == "admin_products")
async def show_products(callback: CallbackQuery, session: AsyncSession) -> None:
    prod_service = ProductService(session)
    cat_service = CategoryService(session)

    products = await prod_service.get_all()
    categories = await cat_service.get_all()

    text = (
        f"📦 <b>Управління товарами</b>\n\n"
        f"Всього товарів: <b>{len(products)}</b>\n\n"
        "Оберіть товар або додайте новий:"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=get_product_list_keyboard(products, categories)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_prod_manage_"))
async def product_actions(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split("_")[-1])
    prod_service = ProductService(session)

    product = await prod_service.get_by_id(product_id)
    if not product:
        await callback.answer("❌ Товар не знайдений", show_alert=True)
        return

    cat_name = f"{product.category.emoji} {product.category.name}" if product.category else "—"
    price_str = format_price(product.price)
    has_photo = "✅ Є" if product.image_path else "❌ Немає"
    available = "✅" if product.is_available else "❌"

    text = (
        f"📦 <b>{product.name}</b>\n\n"
        f"📂 Категорія: {cat_name}\n"
        f"💬 Опис: {product.description or '—'}\n"
        f"💵 Ціна: <b>{price_str}</b>\n"
        f"🖼 Фото: {has_photo}\n"
        f"👁 Доступний: {available}\n\n"
        "Оберіть дію:"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=get_product_actions_keyboard(product_id)
    )
    await callback.answer()


@router.callback_query(F.data == "admin_prod_add")
async def add_product_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    cat_service = CategoryService(session)
    categories = await cat_service.get_all()

    if not categories:
        await callback.answer("❌ Спочатку створіть категорію!", show_alert=True)
        return

    await state.set_state(AdminProductStates.waiting_category)
    await callback.message.edit_text(
        "📦 <b>Додати товар</b>\n\n"
        "Крок 1/5: Оберіть категорію:",
        parse_mode="HTML",
        reply_markup=get_select_category_keyboard(categories, action="new"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("select_cat_new_"), AdminProductStates.waiting_category)
async def add_product_category_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    category_id = int(callback.data.split("_")[-1])
    cat_service = CategoryService(session)
    category = await cat_service.get_by_id(category_id)

    await state.update_data(new_product_category_id=category_id)
    await state.set_state(AdminProductStates.waiting_name)

    await callback.message.edit_text(
        f"📦 <b>Додати товар</b>\n\n"
        f"✅ Категорія: {category.emoji} <b>{category.name}</b>\n\n"
        "Крок 2/5: Введіть назву товару:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_prod_add"),
    )
    await callback.answer()


@router.message(AdminProductStates.waiting_name)
async def add_product_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) < 1 or len(name) > 200:
        await message.answer("❌ Назва повинна бути від 1 до 200 символів. Спробуйте ще раз:")
        return

    await state.update_data(new_product_name=name)
    await state.set_state(AdminProductStates.waiting_description)

    await message.answer(
        f"✅ Назва: <b>{name}</b>\n\n"
        "Крок 3/5: Введіть опис товару:\n\n"
        "<i>Або натисніть /skip щоб пропустити</i>",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_products"),
    )


@router.message(AdminProductStates.waiting_description)
async def add_product_description(message: Message, state: FSMContext) -> None:
    if message.text and message.text.strip() == "/skip":
        description = None
    else:
        description = message.text.strip() if message.text else None

    await state.update_data(new_product_description=description)
    await state.set_state(AdminProductStates.waiting_price)

    await message.answer(
        f"✅ Опис: {description or '<i>без опису</i>'}\n\n"
        "Крок 4/5: Введіть ціну (наприклад: 150 або 99.50):",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_products"),
    )


@router.message(AdminProductStates.waiting_price)
async def add_product_price(message: Message, state: FSMContext) -> None:
    price = validate_price(message.text or "")
    if price is None:
        await message.answer(
            "❌ <b>Невірний формат ціни</b>\n\n"
            "Введіть число, наприклад: <code>150</code> або <code>99.50</code>",
            parse_mode="HTML",
        )
        return

    await state.update_data(new_product_price=price)
    await state.set_state(AdminProductStates.waiting_photo)

    price_str = format_price(price)
    await message.answer(
        f"✅ Ціна: <b>{price_str}</b>\n\n"
        "Крок 5/5: Надішліть фото товару:\n\n"
        "<i>Або натисніть /skip щоб пропустити</i>",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_products"),
    )


@router.message(AdminProductStates.waiting_photo, F.photo)
async def add_product_photo(message: Message, state: FSMContext, session: AsyncSession) -> None:
    photo = message.photo[-1]
    image_path = await save_photo(message.bot, photo)

    data = await state.get_data()
    await _create_product(message, state, session, data, image_path)


@router.message(AdminProductStates.waiting_photo, F.text == "/skip")
async def add_product_skip_photo(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await _create_product(message, state, session, data, image_path=None)


@router.message(AdminProductStates.waiting_photo)
async def add_product_invalid_photo(message: Message) -> None:
    await message.answer(
        "❌ <b>Будь ласка, надішліть фото</b>\n\n"
        "Або натисніть /skip щоб пропустити",
        parse_mode="HTML",
    )


async def _create_product(message: Message, state: FSMContext, session: AsyncSession, data: dict, image_path: str | None) -> None:
    prod_service = ProductService(session)
    cat_service = CategoryService(session)

    product = await prod_service.create(
        category_id=data["new_product_category_id"],
        name=data["new_product_name"],
        description=data.get("new_product_description"),
        price=data["new_product_price"],
        image_path=image_path,
    )

    await state.clear()

    products = await prod_service.get_all()
    categories = await cat_service.get_all()

    photo_status = "✅ Фото є" if image_path else "❌ Без фото"
    await message.answer(
        f"✅ <b>Товар успішно створено!</b>\n\n"
        f"📦 <b>{product.name}</b>\n"
        f"💵 {format_price(product.price)}\n"
        f"🖼 {photo_status}",
        parse_mode="HTML",
        reply_markup=get_product_list_keyboard(products, categories),
    )
    logger.info(f"Product created: {product.id} - {product.name}")


@router.callback_query(F.data.startswith("admin_prod_edit_"))
async def edit_product_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split("_")[-1])
    prod_service = ProductService(session)
    product = await prod_service.get_by_id(product_id)

    if not product:
        await callback.answer("❌ Товар не знайдений", show_alert=True)
        return

    await callback.message.edit_text(
        f"✏️ <b>Редагувати: {product.name}</b>\n\n"
        "Оберіть поле для редагування:",
        parse_mode="HTML",
        reply_markup=get_product_edit_fields_keyboard(product_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field_name_"))
async def edit_product_name_start(callback: CallbackQuery, state: FSMContext) -> None:
    product_id = int(callback.data.split("_")[-1])
    await state.set_state(AdminProductStates.edit_name)
    await state.update_data(edit_product_id=product_id)
    await callback.message.edit_text(
        "✏️ <b>Редагувати назву</b>\n\nВведіть нову назву товару:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard(f"admin_prod_edit_{product_id}"),
    )
    await callback.answer()


@router.message(AdminProductStates.edit_name)
async def edit_product_name_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = message.text.strip()
    if len(name) < 1 or len(name) > 200:
        await message.answer("❌ Назва від 1 до 200 символів. Спробуйте ще раз:")
        return

    data = await state.get_data()
    product_id = data["edit_product_id"]

    prod_service = ProductService(session)
    product = await prod_service.update(product_id, name=name)
    await state.clear()

    cat_service = CategoryService(session)
    products = await prod_service.get_all()
    categories = await cat_service.get_all()

    await message.answer(
        f"✅ <b>Назву змінено на:</b> {name}",
        parse_mode="HTML",
        reply_markup=get_product_list_keyboard(products, categories),
    )


@router.callback_query(F.data.startswith("edit_field_desc_"))
async def edit_product_desc_start(callback: CallbackQuery, state: FSMContext) -> None:
    product_id = int(callback.data.split("_")[-1])
    await state.set_state(AdminProductStates.edit_description)
    await state.update_data(edit_product_id=product_id)
    await callback.message.edit_text(
        "✏️ <b>Редагувати опис</b>\n\nВведіть новий опис товару:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard(f"admin_prod_edit_{product_id}"),
    )
    await callback.answer()


@router.message(AdminProductStates.edit_description)
async def edit_product_desc_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    description = message.text.strip() if message.text else ""
    data = await state.get_data()
    product_id = data["edit_product_id"]

    prod_service = ProductService(session)
    await prod_service.update(product_id, description=description)
    await state.clear()

    cat_service = CategoryService(session)
    products = await prod_service.get_all()
    categories = await cat_service.get_all()

    await message.answer(
        f"✅ <b>Опис оновлено</b>",
        parse_mode="HTML",
        reply_markup=get_product_list_keyboard(products, categories),
    )


@router.callback_query(F.data.startswith("edit_field_price_"))
async def edit_product_price_start(callback: CallbackQuery, state: FSMContext) -> None:
    product_id = int(callback.data.split("_")[-1])
    await state.set_state(AdminProductStates.edit_price)
    await state.update_data(edit_product_id=product_id)
    await callback.message.edit_text(
        "✏️ <b>Редагувати ціну</b>\n\nВведіть нову ціну:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard(f"admin_prod_edit_{product_id}"),
    )
    await callback.answer()


@router.message(AdminProductStates.edit_price)
async def edit_product_price_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    price = validate_price(message.text or "")
    if price is None:
        await message.answer(
            "❌ Невірний формат ціни. Введіть число, наприклад: <code>150</code>",
            parse_mode="HTML",
        )
        return

    data = await state.get_data()
    product_id = data["edit_product_id"]

    prod_service = ProductService(session)
    await prod_service.update(product_id, price=price)
    await state.clear()

    cat_service = CategoryService(session)
    products = await prod_service.get_all()
    categories = await cat_service.get_all()

    await message.answer(
        f"✅ <b>Ціну змінено на:</b> {format_price(price)}",
        parse_mode="HTML",
        reply_markup=get_product_list_keyboard(products, categories),
    )


@router.callback_query(F.data.startswith("edit_field_photo_"))
async def edit_product_photo_start(callback: CallbackQuery, state: FSMContext) -> None:
    product_id = int(callback.data.split("_")[-1])
    await state.set_state(AdminProductStates.edit_photo)
    await state.update_data(edit_product_id=product_id)
    await callback.message.edit_text(
        "✏️ <b>Редагувати фото</b>\n\nНадішліть нове фото товару:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard(f"admin_prod_edit_{product_id}"),
    )
    await callback.answer()


@router.message(AdminProductStates.edit_photo, F.photo)
async def edit_product_photo_process(message: Message, state: FSMContext, session: AsyncSession) -> None:
    photo = message.photo[-1]
    data = await state.get_data()
    product_id = data["edit_product_id"]

    prod_service = ProductService(session)
    old_product = await prod_service.get_by_id(product_id)
    old_path = old_product.image_path if old_product else None

    image_path = await save_photo(message.bot, photo)
    await prod_service.update(product_id, image_path=image_path)

    if old_path:
        delete_photo(old_path)

    await state.clear()

    cat_service = CategoryService(session)
    products = await prod_service.get_all()
    categories = await cat_service.get_all()

    await message.answer(
        f"✅ <b>Фото оновлено!</b>",
        parse_mode="HTML",
        reply_markup=get_product_list_keyboard(products, categories),
    )


@router.message(AdminProductStates.edit_photo)
async def edit_product_photo_invalid(message: Message) -> None:
    await message.answer("❌ Надішліть фото (не файл, а саме фотографію).")


@router.callback_query(F.data.startswith("admin_prod_delete_"))
async def delete_product_confirm(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split("_")[-1])
    prod_service = ProductService(session)
    product = await prod_service.get_by_id(product_id)

    if not product:
        await callback.answer("❌ Товар не знайдений", show_alert=True)
        return

    text = (
        f"🗑 <b>Видалити товар?</b>\n\n"
        f"📦 <b>{product.name}</b>\n"
        f"💵 {format_price(product.price)}\n\n"
        "Ви впевнені?"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=get_confirm_delete_keyboard("prod", product_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_prod_"))
async def delete_product_execute(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split("_")[-1])
    prod_service = ProductService(session)

    product = await prod_service.get_by_id(product_id)
    old_path = product.image_path if product else None
    name = product.name if product else "невідомий"

    success = await prod_service.delete(product_id)

    if success:
        if old_path:
            delete_photo(old_path)

        cat_service = CategoryService(session)
        products = await prod_service.get_all()
        categories = await cat_service.get_all()

        await callback.message.edit_text(
            f"✅ <b>Товар видалено:</b> {name}",
            parse_mode="HTML",
            reply_markup=get_product_list_keyboard(products, categories),
        )
        logger.info(f"Product {product_id} deleted")
    else:
        await callback.answer("❌ Помилка видалення", show_alert=True)


@router.callback_query(F.data.startswith("cancel_delete_prod_"))
async def cancel_delete_product(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split("_")[-1])
    prod_service = ProductService(session)
    product = await prod_service.get_by_id(product_id)

    if product:
        cat_name = f"{product.category.emoji} {product.category.name}" if product.category else "—"
        text = (
            f"📦 <b>{product.name}</b>\n\n"
            f"📂 Категорія: {cat_name}\n"
            f"💵 Ціна: {format_price(product.price)}\n\n"
            "Оберіть дію:"
        )
        await callback.message.edit_text(
            text, parse_mode="HTML",
            reply_markup=get_product_actions_keyboard(product_id)
        )
    await callback.answer("Скасовано")
