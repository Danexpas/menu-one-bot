from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.models.category import Category
from bot.models.product import Product


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📂 Категорії", callback_data="admin_categories")
    builder.button(text="📦 Товари", callback_data="admin_products")
    builder.button(text="ℹ️ Про нас", callback_data="admin_about")
    builder.button(text="📞 Контакти", callback_data="admin_contacts")
    builder.button(text="⚙️ Налаштування", callback_data="admin_settings")
    builder.button(text="🔑 Змінити пароль", callback_data="admin_change_password")
    builder.button(text="❌ Вийти", callback_data="admin_exit")
    builder.adjust(2, 2, 1, 1, 1)
    return builder.as_markup()


def get_category_list_keyboard(categories: list[Category], action: str = "manage") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"{cat.emoji} {cat.name}",
            callback_data=f"admin_cat_{action}_{cat.id}"
        )
    builder.button(text="➕ Додати категорію", callback_data="admin_cat_add")
    builder.button(text="🔙 Назад", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_category_actions_keyboard(category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Перейменувати", callback_data=f"admin_cat_rename_{category_id}")
    builder.button(text="🗑 Видалити", callback_data=f"admin_cat_delete_{category_id}")
    builder.button(text="🔙 Назад", callback_data="admin_categories")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_confirm_delete_keyboard(entity: str, entity_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Так, видалити", callback_data=f"confirm_delete_{entity}_{entity_id}")
    builder.button(text="❌ Скасувати", callback_data=f"cancel_delete_{entity}_{entity_id}")
    builder.adjust(2)
    return builder.as_markup()


def get_product_list_keyboard(products: list[Product], categories: list[Category]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for prod in products:
        cat = next((c for c in categories if c.id == prod.category_id), None)
        cat_name = f"[{cat.emoji}]" if cat else ""
        builder.button(
            text=f"{cat_name} {prod.name} — {prod.price:.0f} ₴",
            callback_data=f"admin_prod_manage_{prod.id}"
        )
    builder.button(text="➕ Додати товар", callback_data="admin_prod_add")
    builder.button(text="🔙 Назад", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редагувати", callback_data=f"admin_prod_edit_{product_id}")
    builder.button(text="🗑 Видалити", callback_data=f"admin_prod_delete_{product_id}")
    builder.button(text="🔙 Назад", callback_data="admin_products")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_product_edit_fields_keyboard(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Назва", callback_data=f"edit_field_name_{product_id}")
    builder.button(text="💬 Опис", callback_data=f"edit_field_desc_{product_id}")
    builder.button(text="💵 Ціна", callback_data=f"edit_field_price_{product_id}")
    builder.button(text="🖼 Фото", callback_data=f"edit_field_photo_{product_id}")
    builder.button(text="🔙 Назад", callback_data=f"admin_prod_manage_{product_id}")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_select_category_keyboard(categories: list[Category], action: str = "add") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"{cat.emoji} {cat.name}",
            callback_data=f"select_cat_{action}_{cat.id}"
        )
    builder.button(text="❌ Скасувати", callback_data="admin_products")
    builder.adjust(2, repeat=True)
    builder.adjust(*([2] * ((len(categories)) // 2 + (len(categories)) % 2)), 1)
    return builder.as_markup()


def get_contacts_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Телефон", callback_data="admin_edit_phone")
    builder.button(text="📸 Instagram", callback_data="admin_edit_instagram")
    builder.button(text="✈️ Telegram", callback_data="admin_edit_telegram")
    builder.button(text="📍 Адреса", callback_data="admin_edit_address")
    builder.button(text="🕐 Графік роботи", callback_data="admin_edit_schedule")
    builder.button(text="🔙 Назад", callback_data="admin_menu")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def get_settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏪 Назва магазину", callback_data="admin_edit_shop_name")
    builder.button(text="👋 Текст привітання", callback_data="admin_edit_welcome")
    builder.button(text="🛒 Інфо про замовлення", callback_data="admin_edit_order_info")
    builder.button(text="🔙 Назад", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_back_keyboard(callback: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data=callback)
    return builder.as_markup()
