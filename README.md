# 🍰 Sweet Paradise — Telegram Bot

> Сучасний Telegram-бот каталог для малого бізнесу (кондитерська, магазин, послуги).
> Повністю готовий до production: каталог з фото, кошик, адмін-панель, SQLite.

[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-blue)](https://docs.aiogram.dev)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)](https://sqlalchemy.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## ✨ Можливості

| Розділ | Що вміє |
|---|---|
| 📦 **Каталог** | Категорії → товари → картка з фото, ціною, описом |
| 🛒 **Кошик** | Додати/видалити/змінити кількість, оформити замовлення |
| ℹ️ **Про нас** | Редагований текст з HTML-форматуванням |
| 📞 **Контакти** | Телефон, Instagram, Telegram, адреса, графік |
| 🔐 **Адмін-панель** | Повне управління через `/admin` + FSM |

### Адмін-панель (`/admin`)
- **Категорії** — додати / перейменувати / видалити
- **Товари** — додати з фото / редагувати / видалити
- **Про нас** — редагування тексту
- **Контакти** — всі поля
- **Налаштування** — назва магазину, текст привітання
- **Пароль** — зміна пароля адміна

---

## 🚀 Швидкий старт

### 1. Клонуйте репозиторій

```bash
git clone https://github.com/Danexpas/menu-one-bot.git
cd menu-one-bot
```

### 2. Створіть віртуальне середовище

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Встановіть залежності

```bash
pip install -r requirements.txt
```

### 4. Налаштуйте `.env`

```bash
cp .env.example .env
```

Відредагуйте `.env`:

```env
BOT_TOKEN=ваш_токен_від_@BotFather
ADMIN_PASSWORD=ваш_пароль
```

> Токен отримайте у [@BotFather](https://t.me/BotFather) → `/newbot`

### 5. Запустіть

```bash
python main.py
```

Бот стартує, автоматично створить таблиці БД і виведе:
```
INFO | Bot started: @your_bot (123456789)
INFO | Run polling for bot @your_bot
```

---

## 🐳 Docker

```bash
# Створіть .env (крок 4 вище)
docker-compose up -d

# Логи
docker-compose logs -f

# Зупинити
docker-compose down
```

---

## 📁 Структура проекту

```
menu-one-bot/
├── main.py                        # Точка входу
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── seed_photos.py                 # Генерація тестових фото
├── test_navigation.py             # Тест навігації (80 перевірок)
├── test_cart.py                   # Тест кошика (44 перевірки)
└── bot/
    ├── config/
    │   └── settings.py            # Конфіг з .env
    ├── database/
    │   ├── base.py                # DeclarativeBase
    │   └── session.py             # AsyncEngine, create_tables()
    ├── models/
    │   ├── category.py            # Категорії
    │   ├── product.py             # Товари
    │   ├── settings.py            # Key-value налаштування
    │   └── cart.py                # Кошик (user_id + product_id + qty)
    ├── services/
    │   ├── category_service.py
    │   ├── product_service.py
    │   ├── settings_service.py
    │   └── cart_service.py
    ├── handlers/
    │   ├── start.py               # /start, головне меню
    │   ├── catalog.py             # Каталог, категорії, товари
    │   ├── cart.py                # Кошик
    │   ├── about.py
    │   ├── contacts.py
    │   └── admin/
    │       ├── auth.py            # /admin + пароль
    │       ├── categories.py
    │       ├── products.py
    │       └── settings.py
    ├── keyboards/
    │   ├── main_kb.py             # Головне меню (з лічильником кошика)
    │   ├── catalog_kb.py
    │   ├── cart_kb.py             # Кошик з ➖ × ➕ 🗑 Видалити
    │   └── admin_kb.py
    ├── states/
    │   └── admin_states.py        # FSM: Auth, Category, Product, Settings
    ├── middlewares/
    │   └── db_middleware.py       # Автоматична передача сесії в handlers
    └── utils/
        └── helpers.py             # save_photo, validate_price, format_price
```

---

## 🗄️ База даних

| Таблиця | Поля |
|---|---|
| `categories` | id, name, emoji, position |
| `products` | id, category_id, name, description, price, image_path, is_available |
| `settings` | id, key, value (key-value store) |
| `cart_items` | id, user_id, product_id, quantity |

БД створюється автоматично при першому запуску. Дані зберігаються після перезапуску.

---

## 🛠️ Технології

| | Версія |
|---|---|
| Python | 3.12+ |
| aiogram | 3.x |
| SQLAlchemy | 2.0 |
| aiosqlite | 0.20 |
| python-dotenv | 1.0 |
| Pillow | 10+ |
| aiofiles | 24.1 |

---

## 🔐 Адмін-панель

```
/admin → пароль (за замовчуванням: admin123)
```

Після входу доступні розділи:

```
📂 Категорії    📦 Товари
ℹ️ Про нас      📞 Контакти
⚙️ Налаштування 🔑 Змінити пароль
```

---

## 📝 Тестування

```bash
# Навігація каталогу (80 перевірок)
python test_navigation.py

# Кошик (44 перевірки)
python test_cart.py
```

---

## 📄 Ліцензія

MIT © 2026 Danexpas
