# 🏪 Menu One Bot

Сучасний Telegram-бот-каталог для малого бізнесу. Побудований на aiogram 3, SQLAlchemy + SQLite, з повноцінною адмін-панеллю.

## ✨ Можливості

- **Каталог товарів** — категорії → товари → картка з фото
- **Про нас** — редагований текст
- **Контакти** — телефон, Instagram, Telegram, адреса, графік
- **Адмін-панель** — повне управління через `/admin`
- **FSM** — стани для всіх форм введення
- **SQLite** — всі дані зберігаються після перезапуску

## 🚀 Встановлення та запуск

### 1. Клонуйте або розпакуйте проект

```bash
cd menu_one_bot
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

Скопіюйте приклад і вставте свій токен:

```bash
cp .env.example .env
```

Відкрийте `.env` і заповніть:

```env
BOT_TOKEN=1234567890:AABBccDDeeffGGhhIIjjKKll  # Токен від @BotFather
ADMIN_PASSWORD=your_secret_password             # Пароль для /admin
DATABASE_URL=sqlite+aiosqlite:///./data/bot.db
MEDIA_DIR=./media/products
LOG_LEVEL=INFO
```

> Токен отримайте в [@BotFather](https://t.me/BotFather) через команду `/newbot`

### 5. Запустіть бота

```bash
python main.py
```

---

## 🐳 Запуск через Docker

### 1. Створіть `.env` файл (як описано вище)

### 2. Запустіть

```bash
docker-compose up -d
```

### 3. Перегляд логів

```bash
docker-compose logs -f
```

### 4. Зупинка

```bash
docker-compose down
```

---

## 🔐 Адмін-панель

1. Відправте боту команду `/admin`
2. Введіть пароль (за замовчуванням: `admin123`)
3. Управляйте:
   - **Категоріями** — додавання, перейменування, видалення
   - **Товарами** — додавання з фото, редагування, видалення
   - **«Про нас»** — редагування тексту
   - **Контактами** — телефон, соцмережі, адреса, графік
   - **Налаштуваннями** — назва магазину, текст привітання
   - **Паролем** — зміна пароля адміна

---

## 📁 Структура проекту

```
menu_one_bot/
├── main.py                    # Точка входу
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── data/                      # SQLite база даних (auto-created)
├── media/products/            # Фото товарів (auto-created)
└── bot/
    ├── config/
    │   └── settings.py        # Pydantic settings з .env
    ├── database/
    │   ├── base.py            # DeclarativeBase
    │   └── session.py         # Engine, session factory
    ├── models/
    │   ├── category.py
    │   ├── product.py
    │   └── settings.py
    ├── services/
    │   ├── category_service.py
    │   ├── product_service.py
    │   └── settings_service.py
    ├── handlers/
    │   ├── start.py           # /start, головне меню
    │   ├── catalog.py         # Каталог, категорії, товари
    │   ├── about.py           # Про нас
    │   ├── contacts.py        # Контакти
    │   └── admin/
    │       ├── auth.py        # /admin, логін
    │       ├── categories.py  # Управління категоріями
    │       ├── products.py    # Управління товарами
    │       └── settings.py    # Контакти, про нас, пароль
    ├── keyboards/
    │   ├── main_kb.py
    │   ├── catalog_kb.py
    │   └── admin_kb.py
    ├── states/
    │   └── admin_states.py    # FSM стани
    ├── middlewares/
    │   └── db_middleware.py   # Передача сесії БД в handlers
    └── utils/
        └── helpers.py         # save_photo, validate_price, ...
```

---

## 🛠 Технології

| Технологія | Версія | Призначення |
|---|---|---|
| Python | 3.12 | Мова програмування |
| aiogram | 3.13 | Telegram Bot Framework |
| SQLAlchemy | 2.0 | ORM |
| aiosqlite | 0.20 | Async SQLite driver |
| pydantic-settings | 2.6 | Конфігурація через .env |
| aiofiles | 24.1 | Async файлові операції |
