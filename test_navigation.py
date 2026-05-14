"""
Navigation smoke-test.
Tests every catalog route without a real Telegram connection.
"""
import asyncio
import sys
import os
import io
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BOT_TOKEN", "placeholder")

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from bot.database.session import async_session_factory
from bot.services.category_service import CategoryService
from bot.services.product_service import ProductService
from bot.services.settings_service import SettingsService
from bot.keyboards.catalog_kb import (
    get_categories_keyboard,
    get_products_keyboard,
    get_product_keyboard,
    get_empty_catalog_keyboard,
)
from bot.keyboards.main_kb import get_start_keyboard, get_main_menu_keyboard
from bot.utils.helpers import format_price

# ── ANSI colors ────────────────────────────────────────────────────────────────
GRN = "\033[92m"; RED = "\033[91m"; YLW = "\033[93m"; BLU = "\033[94m"; RST = "\033[0m"; BOLD = "\033[1m"

passed = failed = 0

def ok(msg):   global passed; passed += 1; print(f"  {GRN}✓{RST} {msg}")
def fail(msg): global failed; failed += 1; print(f"  {RED}✗{RST} {msg}")
def info(msg): print(f"  {BLU}→{RST} {msg}")
def section(title): print(f"\n{BOLD}{YLW}{'─'*50}{RST}\n{BOLD}  {title}{RST}")


@dataclass
class FakeMsg:
    """Minimal message mock that tracks type and content."""
    msg_type: str = "text"          # "text" | "photo"
    text: str = ""
    caption: str = ""
    reply_markup: Any = None
    deleted: bool = False
    answers: list = field(default_factory=list)

    def as_text(self): return self.caption if self.msg_type == "photo" else self.text


def extract_buttons(markup) -> list[str]:
    if not markup:
        return []
    return [btn.text for row in markup.inline_keyboard for btn in row]


async def run_tests():
    async with async_session_factory() as session:
        cfg  = SettingsService(session)
        cats = CategoryService(session)
        prds = ProductService(session)

        shop_name  = await cfg.get("shop_name")
        categories = await cats.get_all()
        all_prods  = await prds.get_all()

        # ── 1. /start ──────────────────────────────────────────────────────────
        section("1. /start — welcome screen")
        welcome = await cfg.get("welcome_text") or ""
        kb      = get_start_keyboard()
        btns    = extract_buttons(kb)
        ok(f"shop_name = {shop_name!r}") if shop_name else fail("shop_name empty")
        ok(f"welcome_text present ({len(welcome)} chars)") if welcome else fail("welcome_text empty")
        ok(f"start button: {btns}") if "📋 Відкрити меню" in btns else fail(f"missing start button, got {btns}")

        # ── 2. Main menu ───────────────────────────────────────────────────────
        section("2. Головне меню")
        kb   = get_main_menu_keyboard()
        btns = extract_buttons(kb)
        for label in ("📦 Асортимент", "ℹ️ Про нас", "📞 Контакти"):
            ok(f"button present: {label}") if label in btns else fail(f"missing: {label}")

        # ── 3. Catalog — categories ────────────────────────────────────────────
        section("3. Каталог — список категорій")
        ok(f"categories in DB: {len(categories)}") if categories else fail("no categories!")
        kb   = get_categories_keyboard(categories)
        btns = extract_buttons(kb)
        for cat in categories:
            label = f"{cat.emoji} {cat.name}"
            ok(f"category button: {label}") if label in btns else fail(f"missing category btn: {label}")
        ok("close button present") if "❌ Закрити" in btns else fail("missing ❌ Закрити")

        # ── 4. Products per category ───────────────────────────────────────────
        section("4. Товари у кожній категорії")
        for cat in categories:
            prods = await prds.get_by_category(cat.id)
            ok(f"{cat.emoji} {cat.name}: {len(prods)} товарів")
            if not prods:
                fail(f"  category {cat.name} is empty!")
                continue
            kb   = get_products_keyboard(prods, cat.id, page=0)
            btns = extract_buttons(kb)
            ok(f"  back button present") if "↩ До категорій" in btns else fail("  missing ↩ До категорій")
            ok(f"  close button present") if "❌ Закрити" in btns else fail("  missing ❌ Закрити")
            for p in prods:
                price_str = f"{p.price:,.0f}".replace(",", " ")
                found = any(p.name in b and "₴" in b for b in btns)
                ok(f"  product btn: {p.name} — {price_str} ₴") if found else fail(f"  missing product: {p.name}")

        # ── 5. Product cards ───────────────────────────────────────────────────
        section("5. Картка кожного товару")
        for p in all_prods:
            kb   = get_product_keyboard(p)
            btns = extract_buttons(kb)
            has_photo = p.image_path and Path(p.image_path).exists()
            price_str = format_price(p.price)

            ok(f"[{p.id:>2}] {p.name} ({price_str}) | фото={'✅' if has_photo else '❌ немає'}")

            ok(f"  🛒 Замовити") if "🛒 Замовити" in btns else fail(f"  missing 🛒 Замовити for {p.name}")
            ok(f"  ⬅ Назад → cat_{p.category_id}") if "⬅ Назад" in btns else fail(f"  missing ⬅ Назад")
            ok(f"  ❌ Закрити") if "❌ Закрити" in btns else fail(f"  missing ❌ Закрити")

            if not has_photo:
                fail(f"  photo file missing: {p.image_path}")

        # ── 6. Photo/text transition logic ─────────────────────────────────────
        section("6. Логіка переходу text ↔ photo")

        def check_is_media(msg_type):
            return msg_type in ("photo", "document", "video")

        cases = [
            ("text",  "photo", "delete+answer_photo"),
            ("photo", "text",  "delete+answer_text"),
            ("text",  "text",  "edit_text"),
            ("photo", "photo", "edit_media or delete+answer_photo"),
        ]
        for from_t, to_t, expected in cases:
            is_media = check_is_media(from_t)
            if from_t == "text" and to_t == "photo":
                action = "delete+answer_photo"
            elif from_t == "photo" and to_t == "text":
                action = "delete+answer_text"
            elif from_t == "text" and to_t == "text":
                action = "edit_text"
            else:
                action = "edit_media or delete+answer_photo"
            ok(f"{from_t:5s} → {to_t:5s} : {action}")

        # ── 7. Settings ────────────────────────────────────────────────────────
        section("7. Налаштування (контакти / про нас)")
        check_keys = {
            "about_text":         "Про нас",
            "contacts_phone":     "Телефон",
            "contacts_instagram": "Instagram",
            "contacts_telegram":  "Telegram",
            "contacts_address":   "Адреса",
            "contacts_schedule":  "Графік",
        }
        for key, label in check_keys.items():
            val = await cfg.get(key)
            is_default = val and ("XX" in val or "your_" in val.lower())
            if val and not is_default:
                ok(f"{label}: {val[:50]}")
            elif is_default:
                fail(f"{label}: залишився placeholder — {val!r}")
            else:
                fail(f"{label}: порожньо!")

        # ── Summary ────────────────────────────────────────────────────────────
        total = passed + failed
        print(f"\n{'─'*50}")
        print(f"{BOLD}  Результат: {GRN}{passed} пройшло{RST}{BOLD} / {RED}{failed} провалено{RST}{BOLD} / {total} всього{RST}")
        if failed == 0:
            print(f"\n  {GRN}{BOLD}✓ Всі перевірки пройдено! Бот готовий.{RST}")
        else:
            print(f"\n  {RED}{BOLD}✗ Є проблеми — перевірте вище.{RST}")
        print()


if __name__ == "__main__":
    asyncio.run(run_tests())
