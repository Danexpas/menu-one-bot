from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.models.cart import CartItem


def get_cart_keyboard(items: list[CartItem]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for item in items:
        name     = item.product.name if item.product else f"#{item.product_id}"
        price    = item.product.price if item.product else 0.0
        subtotal = price * item.quantity
        pid      = item.product_id

        # Рядок 1: назва + сума (широка інфо-кнопка)
        builder.row(
            InlineKeyboardButton(
                text=f"{name}  ·  {subtotal:,.0f} ₴".replace(",", " "),
                callback_data=f"cart_info_{pid}",
            )
        )
        # Рядок 2: ➖ кількість ➕  |  🗑 Видалити
        builder.row(
            InlineKeyboardButton(text="➖",             callback_data=f"cart_dec_{pid}"),
            InlineKeyboardButton(text=f"× {item.quantity}", callback_data=f"cart_info_{pid}"),
            InlineKeyboardButton(text="➕",             callback_data=f"cart_inc_{pid}"),
            InlineKeyboardButton(text="🗑 Видалити",    callback_data=f"cart_del_{pid}"),
        )

    if items:
        builder.row(
            InlineKeyboardButton(text="✅ Оформити замовлення", callback_data="cart_checkout"),
        )
        builder.row(
            InlineKeyboardButton(text="🗑 Очистити кошик",     callback_data="cart_clear"),
            InlineKeyboardButton(text="📦 Продовжити покупки", callback_data="catalog_open"),
        )
        builder.row(
            InlineKeyboardButton(text="🏠 Головне меню", callback_data="open_menu"),
        )
    else:
        builder.row(
            InlineKeyboardButton(text="📦 До каталогу",  callback_data="catalog_open"),
            InlineKeyboardButton(text="🏠 Головне меню", callback_data="open_menu"),
        )

    return builder.as_markup()


def get_product_cart_keyboard(product_id: int, category_id: int, in_cart: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if in_cart:
        builder.row(
            InlineKeyboardButton(text="✅ В кошику", callback_data=f"cart_inc_{product_id}"),
            InlineKeyboardButton(text="➕ Ще одну",  callback_data=f"cart_inc_{product_id}"),
        )
    else:
        builder.row(
            InlineKeyboardButton(text="🛒 В кошик", callback_data=f"cart_add_{product_id}"),
        )
    builder.row(
        InlineKeyboardButton(text="⬅ Назад",   callback_data=f"cat_{category_id}"),
        InlineKeyboardButton(text="❌ Закрити", callback_data="catalog_close"),
    )
    return builder.as_markup()


def get_checkout_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🗑 Очистити після замовлення", callback_data="cart_clear_after_order"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад до кошика", callback_data="cart_view"),
    )
    return builder.as_markup()
