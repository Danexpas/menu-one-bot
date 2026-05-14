from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.models.category import Category
from bot.models.product import Product

ITEMS_PER_PAGE = 8


def get_categories_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"{cat.emoji} {cat.name}",
            callback_data=f"cat_{cat.id}"
        )
    builder.button(text="❌ Закрити", callback_data="catalog_close")
    builder.adjust(2, repeat=True)
    builder.adjust(*([2] * (len(categories) // 2 + len(categories) % 2)), 1)
    return builder.as_markup()


def get_products_keyboard(
    products: list[Product],
    category_id: int,
    page: int = 0,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_products = products[start:end]

    for prod in page_products:
        price_str = f"{prod.price:,.0f}".replace(",", " ")
        builder.button(
            text=f"{prod.name} — {price_str} ₴",
            callback_data=f"prod_{prod.id}"
        )

    nav_row = []
    if page > 0:
        nav_row.append(("⬅ Назад", f"cat_page_{category_id}_{page - 1}"))
    if end < len(products):
        nav_row.append(("Далі ➡", f"cat_page_{category_id}_{page + 1}"))

    builder.adjust(1)

    nav_builder = InlineKeyboardBuilder()
    for text, cb in nav_row:
        nav_builder.button(text=text, callback_data=cb)
    nav_builder.button(text="↩ До категорій", callback_data="catalog_open")
    nav_builder.button(text="❌ Закрити", callback_data="catalog_close")
    nav_builder.adjust(len(nav_row) if nav_row else 1, 2)

    builder.attach(nav_builder)
    return builder.as_markup()


def get_product_keyboard(product: Product) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Замовити", callback_data=f"order_{product.id}")
    builder.button(text="⬅ Назад", callback_data=f"cat_{product.category_id}")
    builder.button(text="❌ Закрити", callback_data="catalog_close")
    builder.adjust(1, 2)
    return builder.as_markup()


def get_empty_catalog_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Закрити", callback_data="catalog_close")
    return builder.as_markup()
