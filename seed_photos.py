"""Generate placeholder product images and attach them to all products in DB."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BOT_TOKEN", "placeholder")

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from bot.database.session import async_session_factory
from bot.services.product_service import ProductService

PALETTES = {
    1: ("#FF6B6B", "#FF8E53"),  # Торти  — теплий червоно-оранжевий
    2: ("#A18CD1", "#FBC2EB"),  # Тістечка — ліловий/рожевий
    3: ("#43E97B", "#38F9D7"),  # Печиво — смарагдово-бірюзовий
}
DEFAULT_PALETTE = ("#F7971E", "#FFD200")

MEDIA_DIR = Path("media/products")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

W, H = 800, 600


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def make_gradient(w: int, h: int, c1, c2) -> Image.Image:
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        col = lerp_color(c1, c2, y / h)
        for x in range(w):
            px[x, y] = col
    return img


def draw_icon(draw: ImageDraw.ImageDraw, cat_id: int, cx: int, cy: int, size: int = 80):
    r = size
    fill = (255, 255, 255, 60)
    stroke = (255, 255, 255, 180)

    if cat_id == 1:  # Торти — шматок торта (трикутник + зубчики)
        pts = [(cx, cy - r), (cx - r, cy + r // 2), (cx + r, cy + r // 2)]
        draw.polygon(pts, fill=stroke)
        # крем зверху
        for i in range(5):
            x0 = cx - r + i * (2 * r // 4)
            draw.ellipse([x0, cy - r - 12, x0 + r // 2, cy - r + 12], fill=stroke)

    elif cat_id == 2:  # Тістечка — зірочка
        points = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            rad = r if i % 2 == 0 else r // 2
            points.append((cx + rad * math.cos(angle), cy + rad * math.sin(angle)))
        draw.polygon(points, fill=stroke)

    else:  # Печиво — коло з крапками
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=stroke)
        dot_r = r // 7
        for dx, dy in [(-r//3, -r//3), (r//3, -r//3), (0, r//4), (-r//4, r//3 + 5), (r//4, r//3 + 5)]:
            draw.ellipse([cx+dx-dot_r, cy+dy-dot_r, cx+dx+dot_r, cy+dy+dot_r],
                         fill=lerp_color((200,100,50),(240,160,80), 0.5))


def draw_text_centered(draw, text, y, font, fill=(255, 255, 255), shadow=True, max_w=W-80):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        candidate = (cur + " " + w).strip()
        bb = draw.textbbox((0, 0), candidate, font=font)
        if (bb[2] - bb[0]) > max_w and cur:
            lines.append(cur)
            cur = w
        else:
            cur = candidate
    if cur:
        lines.append(cur)

    line_h = max((draw.textbbox((0,0), l, font=font)[3] - draw.textbbox((0,0), l, font=font)[1]) for l in lines)
    total_h = len(lines) * (line_h + 6)
    sy = y - total_h // 2

    for i, line in enumerate(lines):
        bb = draw.textbbox((0, 0), line, font=font)
        lw = bb[2] - bb[0]
        x = (W - lw) // 2
        iy = sy + i * (line_h + 6)
        if shadow:
            draw.text((x+2, iy+2), line, font=font, fill=(0,0,0,90))
        draw.text((x, iy), line, font=font, fill=fill)


def make_product_image(name: str, price: float, cat_id: int, product_id: int) -> Path:
    pal = PALETTES.get(cat_id, DEFAULT_PALETTE)
    c1, c2 = hex_to_rgb(pal[0]), hex_to_rgb(pal[1])

    base = make_gradient(W, H, c1, c2).convert("RGBA")

    # soft glow circles
    glow = Image.new("RGBA", (W, H), (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-80, -80, 240, 240), fill=(255,255,255,18))
    gd.ellipse((W-200, H-200, W+80, H+80), fill=(255,255,255,14))
    base = Image.alpha_composite(base, glow)

    # icon layer
    icon_layer = Image.new("RGBA", (W, H), (0,0,0,0))
    id_ = ImageDraw.Draw(icon_layer)
    draw_icon(id_, cat_id, W//2, H//2 - 110, size=72)
    base = Image.alpha_composite(base, icon_layer)

    img = base.convert("RGB")
    draw = ImageDraw.Draw(img)

    # fonts
    font_name = font_price = ImageFont.load_default()
    for fp in ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf",
               "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/calibrib.ttf"]:
        if Path(fp).exists():
            try:
                font_name  = ImageFont.truetype(fp, 52)
                font_price = ImageFont.truetype(fp, 32)
            except Exception:
                pass
            break

    # product name
    draw_text_centered(draw, name, H//2 + 20, font_name, fill=(255,255,255))

    # price pill
    price_text = f"{int(price):,}".replace(",", " ") + " ₴"
    bb = draw.textbbox((0,0), price_text, font=font_price)
    pw, ph = bb[2]-bb[0], bb[3]-bb[1]
    pad_x, pad_y = 24, 12
    rx0 = (W - pw)//2 - pad_x
    ry0 = H//2 + 90
    rx1 = (W + pw)//2 + pad_x
    ry1 = ry0 + ph + pad_y * 2
    # pill bg
    pill = Image.new("RGBA", (W, H), (0,0,0,0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([rx0, ry0, rx1, ry1], radius=24, fill=(255,255,255,210))
    img = Image.alpha_composite(img.convert("RGBA"), pill).convert("RGB")
    draw = ImageDraw.Draw(img)
    price_color = lerp_color(c1, c2, 0.35)
    draw.text(((W-pw)//2, ry0+pad_y), price_text, font=font_price, fill=price_color)

    path = MEDIA_DIR / f"product_{product_id}.jpg"
    img.save(str(path), "JPEG", quality=92)
    return path


async def seed_photos():
    async with async_session_factory() as session:
        svc = ProductService(session)
        products = await svc.get_all()

        for p in products:
            path = make_product_image(p.name, p.price, p.category_id, p.id)
            await svc.update(p.id, image_path=str(path))
            print(f"[{p.id:>2}] cat={p.category_id} -> {path.name}")

    print(f"\nDone! {len(products)} photos generated in {MEDIA_DIR}/")


if __name__ == "__main__":
    asyncio.run(seed_photos())
