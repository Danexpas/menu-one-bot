import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.cart_service import CartService
from bot.services.product_service import ProductService
from bot.services.settings_service import SettingsService
from bot.keyboards.cart_kb import get_cart_keyboard, get_checkout_keyboard
from bot.keyboards.main_kb import get_main_menu_keyboard
from bot.utils.helpers import format_price

logger = logging.getLogger(__name__)
router = Router(name="cart")

DIVIDER = "━" * 22


def _build_cart_text(shop_name: str, items, total_qty: int, total_amount: float) -> str:
    if not items:
        return (
            f"🏪 <b>{shop_name}</b>\n\n"
            f"{DIVIDER}\n\n"
            "🛒 <b>Кошик порожній</b>\n\n"
            "Додайте товари з каталогу 👇"
        )

    lines = [
        f"🏪 <b>{shop_name}</b>",
        "",
        f"{DIVIDER}",
        "",
        "🛒 <b>Ваш кошик:</b>",
        "",
    ]
    for item in items:
        name  = item.product.name if item.product else f"Товар #{item.product_id}"
        price = item.product.price if item.product else 0.0
        subtotal = price * item.quantity
        lines.append(
            f"  <b>{name}</b>\n"
            f"  {format_price(price)} × {item.quantity} = <b>{format_price(subtotal)}</b>"
        )

    lines += [
        "",
        f"{DIVIDER}",
        "",
        f"📦 Позицій: <b>{len(items)}</b>  |  Одиниць: <b>{total_qty}</b>",
        f"💵 Сума: <b>{format_price(total_amount)}</b>",
    ]
    return "\n".join(lines)


async def _refresh_cart(callback: CallbackQuery, session: AsyncSession) -> None:
    user_id = callback.from_user.id
    svc     = CartService(session)
    cfg     = SettingsService(session)

    items             = await svc.get_items(user_id)
    total_qty, total  = await svc.total(user_id)
    shop_name         = await cfg.get("shop_name") or "Магазин"
    text              = _build_cart_text(shop_name, items, total_qty, total)
    kb                = get_cart_keyboard(items)

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except TelegramBadRequest:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)


# ── Переглянути кошик ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "cart_view")
async def cart_view(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    await _refresh_cart(callback, session)


# ── Додати товар ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cart_add_"))
async def cart_add(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split("_")[-1])
    svc        = CartService(session)
    item       = await svc.add(callback.from_user.id, product_id)

    prod = await ProductService(session).get_by_id(product_id)
    name = prod.name if prod else f"#{product_id}"
    count = await svc.count(callback.from_user.id)

    await callback.answer(f"✅ {name} додано до кошика!", show_alert=False)

    # Оновити кнопки картки товару
    from bot.keyboards.cart_kb import get_product_cart_keyboard
    if prod:
        kb = get_product_cart_keyboard(product_id, prod.category_id, in_cart=True)
        try:
            await callback.message.edit_reply_markup(reply_markup=kb)
        except TelegramBadRequest:
            pass
    logger.info(f"User {callback.from_user.id} added product {product_id} to cart")


# ── Збільшити кількість ────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cart_inc_"))
async def cart_inc(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split("_")[-1])
    svc        = CartService(session)
    item       = await svc.add(callback.from_user.id, product_id)

    prod = await ProductService(session).get_by_id(product_id)
    name = prod.name if prod else f"#{product_id}"
    await callback.answer(f"➕ {name}: {item.quantity} шт.")

    # якщо викликано з кошика — оновити весь кошик
    if callback.message.text and "Ваш кошик" in (callback.message.text or ""):
        await _refresh_cart(callback, session)


# ── Зменшити кількість ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cart_dec_"))
async def cart_dec(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split("_")[-1])
    svc        = CartService(session)
    await svc.remove_one(callback.from_user.id, product_id)

    items = await svc.get_items(callback.from_user.id)
    item  = next((i for i in items if i.product_id == product_id), None)
    if item:
        await callback.answer(f"➖ {item.product.name}: {item.quantity} шт.")
    else:
        await callback.answer("Товар видалено з кошика")
    await _refresh_cart(callback, session)


# ── Видалити позицію ───────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cart_del_"))
async def cart_del(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split("_")[-1])
    svc        = CartService(session)
    await svc.remove_all(callback.from_user.id, product_id)
    await callback.answer("🗑 Видалено")
    await _refresh_cart(callback, session)


# ── Очистити кошик ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "cart_clear")
async def cart_clear(callback: CallbackQuery, session: AsyncSession) -> None:
    svc   = CartService(session)
    count = await svc.clear(callback.from_user.id)
    await callback.answer(f"🗑 Кошик очищено ({count} позицій)")
    await _refresh_cart(callback, session)
    logger.info(f"User {callback.from_user.id} cleared cart")


@router.callback_query(F.data == "cart_clear_after_order")
async def cart_clear_after_order(callback: CallbackQuery, session: AsyncSession) -> None:
    await CartService(session).clear(callback.from_user.id)
    cfg       = SettingsService(session)
    shop_name = await cfg.get("shop_name") or "Магазин"
    await callback.answer("✅ Кошик очищено")
    await callback.message.edit_text(
        f"🏪 <b>{shop_name}</b>\n\n"
        f"{DIVIDER}\n\n"
        "✅ <b>Дякуємо за замовлення!</b>\n\n"
        "Ваш кошик очищено. Чекайте на зв'язок від нас 😊",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(),
    )


# ── Оформити замовлення ────────────────────────────────────────────────────────

@router.callback_query(F.data == "cart_checkout")
async def cart_checkout(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    svc     = CartService(session)
    cfg     = SettingsService(session)

    items            = await svc.get_items(user_id)
    total_qty, total = await svc.total(user_id)
    shop_name        = await cfg.get("shop_name") or "Магазин"
    phone            = await cfg.get("contacts_phone") or ""
    tg_contact       = await cfg.get("contacts_telegram") or ""
    order_info       = await cfg.get("order_info") or ""

    if not items:
        await callback.answer("❌ Кошик порожній", show_alert=True)
        return

    lines = [
        f"🏪 <b>{shop_name}</b>",
        "",
        f"{DIVIDER}",
        "",
        "✅ <b>Ваше замовлення:</b>",
        "",
    ]
    for item in items:
        name     = item.product.name if item.product else f"#{item.product_id}"
        price    = item.product.price if item.product else 0.0
        subtotal = price * item.quantity
        lines.append(f"  • {name} × {item.quantity} = <b>{format_price(subtotal)}</b>")

    lines += [
        "",
        f"{DIVIDER}",
        f"💵 <b>Разом: {format_price(total)}</b>",
        "",
        "─" * 22,
        "",
        f"📞 {order_info}",
        f"📱 {phone}",
        f"✈️ {tg_contact}",
    ]

    await callback.message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=get_checkout_keyboard(),
    )
    logger.info(f"User {user_id} checked out cart: {len(items)} items, total={total:.2f}")
