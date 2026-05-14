"""Full cart smoke-test — service layer + keyboard layout."""
import asyncio, sys, os, io
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BOT_TOKEN", "placeholder")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from bot.database.session import async_session_factory
from bot.services.cart_service import CartService
from bot.services.product_service import ProductService
from bot.keyboards.cart_kb import get_cart_keyboard, get_product_cart_keyboard
from bot.utils.helpers import format_price

GRN = "\033[92m"; RED = "\033[91m"; YLW = "\033[93m"; BOLD = "\033[1m"; RST = "\033[0m"
passed = failed = 0

def ok(msg):   global passed; passed += 1; print(f"  {GRN}✓{RST} {msg}")
def fail(msg): global failed; failed += 1; print(f"  {RED}✗{RST} {msg}")
def section(t): print(f"\n{BOLD}{YLW}{'─'*52}{RST}\n{BOLD}  {t}{RST}")

def buttons(kb) -> list[str]:
    return [b.text for row in kb.inline_keyboard for b in row]

def rows(kb) -> list[list[str]]:
    return [[b.text for b in row] for row in kb.inline_keyboard]

TEST_USER = 888001

async def run():
    async with async_session_factory() as s:
        cart  = CartService(s)
        prods = await ProductService(s).get_all()
        await cart.clear(TEST_USER)

        p1, p2, p3 = prods[0], prods[1], prods[4]   # Наполеон, Чізкейк, Еклер

        # ── 1. Порожній кошик ─────────────────────────────────────────────────
        section("1. Порожній кошик")
        items = await cart.get_items(TEST_USER)
        qty, total = await cart.total(TEST_USER)
        ok("items = 0")       if len(items) == 0   else fail(f"items={len(items)}")
        ok("qty   = 0")       if qty == 0           else fail(f"qty={qty}")
        ok("total = 0")       if total == 0.0       else fail(f"total={total}")

        kb = get_cart_keyboard([])
        btns = buttons(kb)
        ok("📦 До каталогу")   if "📦 До каталогу"  in btns else fail("missing 📦 До каталогу")
        ok("🏠 Головне меню")  if "🏠 Головне меню" in btns else fail("missing 🏠 Головне меню")
        del_count = sum(1 for t in btns if "🗑 Видалити" in t)
        ok("0 кнопок Видалити в порожньому") if del_count == 0 else fail(f"del={del_count}")

        # ── 2. Додавання товарів ──────────────────────────────────────────────
        section("2. Додавання товарів")
        i1 = await cart.add(TEST_USER, p1.id)
        ok(f"add p1 qty=1: {p1.name}") if i1.quantity == 1 else fail(f"qty={i1.quantity}")

        i1 = await cart.add(TEST_USER, p1.id)
        ok(f"add p1 qty=2 (дублікат)")  if i1.quantity == 2 else fail(f"qty={i1.quantity}")

        i2 = await cart.add(TEST_USER, p2.id)
        i3 = await cart.add(TEST_USER, p3.id)
        ok(f"add p2: {p2.name}")
        ok(f"add p3: {p3.name}")

        items = await cart.get_items(TEST_USER)
        qty, total = await cart.total(TEST_USER)
        expected_total = p1.price*2 + p2.price + p3.price
        ok(f"3 позиції в кошику")       if len(items) == 3            else fail(f"items={len(items)}")
        ok(f"qty={qty} (4 одиниці)")    if qty == 4                   else fail(f"qty={qty}")
        ok(f"total={format_price(total)} вірно") if abs(total - expected_total) < 0.01 else fail(f"total={total} != {expected_total}")

        # ── 3. Клавіатура з 3 позиціями ──────────────────────────────────────
        section("3. Розкладка клавіатури (3 позиції)")
        kb   = get_cart_keyboard(items)
        rs   = rows(kb)
        btns = buttons(kb)

        del_count = sum(1 for t in btns if "🗑 Видалити" in t)
        ok(f"3 кнопки '🗑 Видалити' (по одній на позицію)") if del_count == 3 else fail(f"del={del_count}")

        # Кожен товар: рядок-заголовок + рядок-контролер
        for i, item in enumerate(items):
            name = item.product.name
            # знаходимо рядок із назвою товару
            header_rows = [r for r in rs if any(name in t for t in r)]
            ok(f"рядок назви: {name}") if header_rows else fail(f"рядок не знайдено: {name}")
            # знаходимо рядок контролерів після нього
            idx = rs.index(header_rows[0]) if header_rows else -1
            if idx >= 0 and idx + 1 < len(rs):
                ctrl = rs[idx + 1]
                ok(f"  ➖ присутній")        if "➖"          in ctrl else fail("  ➖ відсутній")
                ok(f"  ➕ присутній")        if "➕"          in ctrl else fail("  ➕ відсутній")
                ok(f"  🗑 Видалити окремо") if any("🗑 Видалити" in t for t in ctrl) else fail("  🗑 Видалити відсутній")

        ok("✅ Оформити замовлення") if "✅ Оформити замовлення" in btns else fail("missing ✅")
        ok("🗑 Очистити кошик")     if "🗑 Очистити кошик"     in btns else fail("missing 🗑 Очистити")
        ok("📦 Продовжити покупки") if "📦 Продовжити покупки" in btns else fail("missing 📦 Продовжити")
        ok("🏠 Головне меню")       if "🏠 Головне меню"       in btns else fail("missing 🏠")

        # ── 4. Зменшити кількість ─────────────────────────────────────────────
        section("4. Зменшити кількість (➖)")
        await cart.remove_one(TEST_USER, p1.id)
        items = await cart.get_items(TEST_USER)
        p1_item = next((i for i in items if i.product_id == p1.id), None)
        ok(f"{p1.name} qty=1 після ➖") if p1_item and p1_item.quantity == 1 else fail(f"qty={p1_item.quantity if p1_item else 'gone'}")

        await cart.remove_one(TEST_USER, p1.id)   # qty 1→0 → має видалитись
        items = await cart.get_items(TEST_USER)
        gone = all(i.product_id != p1.id for i in items)
        ok(f"{p1.name} видалено при qty=0") if gone else fail("товар лишився після qty=0")
        ok(f"залишилось 2 позиції")         if len(items) == 2 else fail(f"items={len(items)}")

        # ── 5. Видалити позицію (🗑 Видалити) ────────────────────────────────
        section("5. Видалити позицію (🗑 Видалити)")
        ok(f"до видалення: {len(items)} позиції")
        removed = await cart.remove_all(TEST_USER, p2.id)
        items = await cart.get_items(TEST_USER)
        ok(f"remove_all повернув True")   if removed                              else fail("remove_all=False")
        ok(f"{p2.name} відсутній")        if all(i.product_id != p2.id for i in items) else fail("товар лишився")
        ok(f"залишилась 1 позиція")       if len(items) == 1                          else fail(f"items={len(items)}")

        # ── 6. Кнопка картки товару ───────────────────────────────────────────
        section("6. Кнопка картки товару")
        kb_out  = get_product_cart_keyboard(p3.id, 2, in_cart=False)
        kb_in   = get_product_cart_keyboard(p3.id, 2, in_cart=True)
        out_btns = buttons(kb_out)
        in_btns  = buttons(kb_in)
        ok("'🛒 В кошик' коли НЕ в кошику") if "🛒 В кошик"   in out_btns else fail(f"out_btns={out_btns}")
        ok("'✅ В кошику' коли В кошику")    if "✅ В кошику"  in in_btns  else fail(f"in_btns={in_btns}")
        ok("'➕ Ще одну' коли В кошику")     if "➕ Ще одну"   in in_btns  else fail(f"in_btns={in_btns}")
        ok("⬅ Назад завжди є")              if "⬅ Назад"      in out_btns else fail("missing ⬅")
        ok("❌ Закрити завжди є")            if "❌ Закрити"   in out_btns else fail("missing ❌")

        # ── 7. Очистити кошик ────────────────────────────────────────────────
        section("7. Очистити кошик")
        # повернемо товар для тесту
        await cart.add(TEST_USER, p1.id)
        cleared = await cart.clear(TEST_USER)
        items   = await cart.get_items(TEST_USER)
        ok(f"clear видалив {cleared} позицій") if cleared >= 1  else fail(f"cleared={cleared}")
        ok("кошик порожній після clear")        if len(items) == 0 else fail(f"items={len(items)}")

        # ── 8. Підсумок ──────────────────────────────────────────────────────
        total_tests = passed + failed
        print(f"\n{'─'*52}")
        print(f"{BOLD}  Результат: {GRN}{passed} пройшло{RST}{BOLD} / {RED}{failed} провалено{RST}{BOLD} / {total_tests} всього{RST}")
        if failed == 0:
            print(f"\n  {GRN}{BOLD}✅ Кошик працює ідеально!{RST}\n")
        else:
            print(f"\n  {RED}{BOLD}❌ Є помилки.{RST}\n")

asyncio.run(run())
