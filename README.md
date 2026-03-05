# TTsavebot

Telegram-бот для скачивания видео из TikTok и Instagram с white-list доступом, SQLite-логированием, Telegram-админкой и `yt-dlp` в качестве downloader backend.

Создатель: Ama

## Возможности

- Принимает ссылки `tiktok.com`, `vm.tiktok.com`, `instagram.com/reel`, `instagram.com/p`.
- Ограничивает доступ по whitelist и ролям `superadmin` / `user`.
- Управляет whitelist прямо из Telegram через `/panel`, `/allow`, `/deny`.
- Сохраняет историю скачиваний и агрегированную статистику в SQLite.
- Очищает временные файлы и режет историю логов до заданного лимита.

## Команды

- `/start`
- `/help`
- `/whoami`
- `/panel`
- `/allow <telegram_id>`
- `/deny <telegram_id>`
- `/stats`
- `/logs`

## Быстрый старт

1. Скопируйте `.env.example` в `.env` и заполните `BOT_TOKEN` и `SUPERADMINS`.
2. Установите зависимости:

```bash
uv sync --dev
```

3. Запустите бота:

```bash
uv run python main.py
```

## Переменные окружения

- `BOT_TOKEN` - токен Telegram-бота.
- `SUPERADMINS` - CSV-список Telegram ID супер-админов.
- `DB_PATH` - путь к SQLite базе, по умолчанию `data/bot.sqlite3`.
- `DOWNLOADS_DIR` - папка временных файлов, по умолчанию `downloads`.
- `YTDLP_BIN` - бинарник `yt-dlp`.
- `YTDLP_TIMEOUT_SECONDS` - timeout загрузки в секундах.
- `MAX_FILE_SIZE_MB` - лимит размера файла для Telegram.
- `INSTAGRAM_COOKIES_PATH` - optional путь к `cookies.txt`.
- `LOG_RETENTION_LIMIT` - максимальное число логов в БД.
- `STALE_FILE_MAX_AGE_HOURS` - возраст для очистки старых файлов.

## Тесты

```bash
uv run pytest
```

## Docker

```bash
docker build -t ttsavebot .
docker run --env-file .env ttsavebot
```

