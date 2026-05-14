from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Відкрити меню", callback_data="open_menu")
    return builder.as_markup()


def get_main_menu_keyboard(cart_count: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Асортимент", callback_data="catalog_open")
    cart_label = f"🛒 Кошик ({cart_count})" if cart_count > 0 else "🛒 Кошик"
    builder.button(text=cart_label, callback_data="cart_view")
    builder.button(text="ℹ️ Про нас", callback_data="about")
    builder.button(text="📞 Контакти", callback_data="contacts")
    builder.adjust(2, 2)
    return builder.as_markup()


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Головне меню", callback_data="open_menu")
    return builder.as_markup()
