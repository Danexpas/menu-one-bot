import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.category_service import CategoryService
from bot.services.product_service import ProductService
from bot.services.settings_service import SettingsService
from bot.services.cart_service import CartService
from bot.keyboards.catalog_kb import (
    get_categories_keyboard,
    get_products_keyboard,
    get_empty_catalog_keyboard,
)
from bot.keyboards.cart_kb import get_product_cart_keyboard
from bot.utils.helpers import format_price

logger = logging.getLogger(__name__)
router = Router(name="catalog")

DIVIDER = "━" * 22


def _header(shop_name: str) -> str:
    return f"🏪 <b>{shop_name}</b>"


def _is_media_message(msg) -> bool:
    return bool(msg.photo or msg.document or msg.video or msg.animation)


async def _show_text(callback: CallbackQuery, text: str, kb) -> None:
    """Show a text message. If current message is media — delete it first."""
    msg = callback.message
    if _is_media_message(msg):
        try:
            await msg.delete()
        except TelegramBadRequest:
            pass
        await msg.answer(text, parse_mode="HTML", reply_markup=kb)
    else:
        try:
            await msg.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except TelegramBadRequest:
            await msg.answer(text, parse_mode="HTML", reply_markup=kb)


async def _show_photo(callback: CallbackQuery, path: str, caption: str, kb) -> None:
    """Show a photo message. If current message already has media — edit it, else delete + send."""
    msg = callback.message
    photo = FSInputFile(path)
    if _is_media_message(msg):
        try:
            await msg.edit_media(
                media=InputMediaPhoto(media=FSInputFile(path), caption=caption, parse_mode="HTML"),
                reply_markup=kb,
            )
            return
        except TelegramBadRequest:
            try:
                await msg.delete()
            except TelegramBadRequest:
                pass
    else:
        try:
            await msg.delete()
        except TelegramBadRequest:
            pass
    await msg.answer_photo(photo=photo, caption=caption, parse_mode="HTML", reply_markup=kb)


# ── Відкрити каталог ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "catalog_open")
async def catalog_open(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()

    cat_service = CategoryService(session)
    settings_service = SettingsService(session)
    categories = await cat_service.get_all()
    shop_name = await settings_service.get("shop_name") or "Магазин"

    if not categories:
        text = (
            f"{_header(shop_name)}\n\n"
            f"{DIVIDER}\n\n"
            "😔 <b>Каталог порожній</b>\n\n"
            "Товари ще не додані."
        )
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_empty_catalog_keyboard())
        return

    lines = [_header(shop_name), "", DIVIDER, "", "📂 <b>Оберіть категорію:</b>", ""]
    for cat in categories:
        lines.append(f"  {cat.emoji} {cat.name}")
    await callback.message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=get_categories_keyboard(categories),
    )


# ── Категорія → список товарів ─────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cat_") & ~F.data.startswith("cat_page_"))
async def show_category(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    category_id = int(callback.data.split("_")[1])

    cat_service = CategoryService(session)
    prod_service = ProductService(session)
    settings_service = SettingsService(session)

    category = await cat_service.get_by_id(category_id)
    if not category:
        await callback.answer("❌ Категорія не знайдена", show_alert=True)
        return

    products = await prod_service.get_by_category(category_id)
    shop_name = await settings_service.get("shop_name") or "Магазин"

    if not products:
        text = (
            f"{_header(shop_name)}\n\n"
            f"{category.emoji} <b>{category.name}</b>\n\n"
            "😔 У цій категорії поки немає товарів."
        )
        await _show_text(callback, text, get_empty_catalog_keyboard())
        return

    text = (
        f"{_header(shop_name)}\n\n"
        f"{DIVIDER}\n\n"
        f"{category.emoji} <b>{category.name}</b>\n\n"
        f"📦 <i>Товарів: {len(products)}</i>\n\n"
        "Оберіть товар 👇"
    )
    await _show_text(callback, text, get_products_keyboard(products, category_id, page=0))


@router.callback_query(F.data.startswith("cat_page_"))
async def show_category_page(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    parts = callback.data.split("_")
    category_id = int(parts[2])
    page = int(parts[3])

    cat_service = CategoryService(session)
    prod_service = ProductService(session)
    settings_service = SettingsService(session)

    category = await cat_service.get_by_id(category_id)
    products = await prod_service.get_by_category(category_id)
    shop_name = await settings_service.get("shop_name") or "Магазин"

    text = (
        f"{_header(shop_name)}\n\n"
        f"{DIVIDER}\n\n"
        f"{category.emoji} <b>{category.name}</b>\n\n"
        f"📦 <i>Товарів: {len(products)}</i>\n\n"
        "Оберіть товар 👇"
    )
    await _show_text(callback, text, get_products_keyboard(products, category_id, page=page))


# ── Картка товару ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("prod_"))
async def show_product(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    product_id = int(callback.data.split("_")[1])

    prod_service = ProductService(session)
    settings_service = SettingsService(session)

    product = await prod_service.get_by_id(product_id)
    if not product:
        await callback.answer("❌ Товар не знайдений", show_alert=True)
        return

    cart_service = CartService(session)
    shop_name = await settings_service.get("shop_name") or "Магазин"
    description = product.description or "<i>Опис відсутній</i>"
    price_str = format_price(product.price)

    cart_items = await cart_service.get_items(callback.from_user.id)
    in_cart = any(i.product_id == product_id for i in cart_items)
    cart_qty = sum(i.quantity for i in cart_items if i.product_id == product_id)

    cart_badge = f"  ·  🛒 {cart_qty} шт." if cart_qty > 0 else ""

    caption = (
        f"{_header(shop_name)}\n\n"
        f"{DIVIDER}\n\n"
        f"<b>{product.name}</b>{cart_badge}\n\n"
        f"💬 {description}\n\n"
        f"💵 <b>{price_str}</b>\n\n"
        f"{DIVIDER}"
    )
    kb = get_product_cart_keyboard(product_id, product.category_id, in_cart=in_cart)

    if product.image_path and Path(product.image_path).exists():
        await _show_photo(callback, product.image_path, caption, kb)
    else:
        await _show_text(callback, caption, kb)


# ── Замовити ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("order_"))
async def order_product(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split("_")[1])
    prod_service = ProductService(session)
    settings_service = SettingsService(session)

    product = await prod_service.get_by_id(product_id)
    order_info = await settings_service.get("order_info") or ""
    phone = await settings_service.get("contacts_phone") or ""
    tg = await settings_service.get("contacts_telegram") or ""

    if product:
        msg = f"🛒 {product.name}\n\n{order_info}\n📱 {phone}\n✈️ {tg}"
        await callback.answer(msg[:200], show_alert=True)
    else:
        await callback.answer("❌ Товар не знайдений", show_alert=True)


# ── Закрити каталог ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "catalog_close")
async def catalog_close(callback: CallbackQuery) -> None:
    await callback.answer("Каталог закрито")
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
