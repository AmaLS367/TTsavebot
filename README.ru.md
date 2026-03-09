<div align="center">

# TTsavebot

Telegram-бот для скачивания медиа по поддерживаемым ссылкам с whitelist-доступом, админ-командами и логированием в SQLite.

[English version](README.md)

</div>

## Кратко

TTsavebot принимает ссылки на TikTok и Instagram Reel/Post, проверяет доступ пользователя, скачивает видео через `yt-dlp`, отправляет результат обратно в Telegram и сохраняет историю операций в SQLite. Проект организован по слоям `presentation / core / infrastructure`, поэтому его проще сопровождать, чем типичный односценарный бот.

## Возможности

| Зона | Что есть сейчас |
| --- | --- |
| Доступ | whitelist-проверка для всех входящих сообщений |
| Загрузка | TikTok и Instagram Reel/Post через `yt-dlp` |
| Админка | `/panel`, `/allow`, `/deny`, `/stats`, `/logs` |
| Логи | SQLite-история попыток, отказов, ошибок и статистики |
| Очистка файлов | удаление временных файлов и cleanup старых артефактов |
| Тесты | unit и integration тесты по основным сценариям |

## Команды

| Команда | Доступ | Назначение |
| --- | --- | --- |
| `/start` | whitelisted users | приветствие и показ текущего Telegram ID |
| `/help` | whitelisted users | список доступных команд по роли |
| `/whoami` | whitelisted users | показать Telegram ID и роль |
| `/panel` | superadmins | открыть inline-админку |
| `/allow <telegram_id>` | superadmins | добавить пользователя в whitelist |
| `/deny <telegram_id>` | superadmins | убрать пользователя из whitelist |
| `/stats` | superadmins | показать агрегированную статистику |
| `/logs` | superadmins | показать последние записи логов |

## Быстрый старт на Windows

```powershell
git clone https://github.com/AmaLS367/TTsavebot.git
cd TTsavebot

py -m pip install uv
Copy-Item .env.example .env
notepad .env

uv sync --dev
uv run python .\main.py
```

## Docker

```powershell
Copy-Item .env.example .env
notepad .env

docker build -t ttsavebot .
docker run --rm --env-file .env ttsavebot
```

## Переменные окружения

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `BOT_TOKEN` | нет | токен Telegram-бота |
| `SUPERADMINS` | нет | CSV-список ID супер-админов |
| `DB_PATH` | `data/bot.sqlite3` | путь к SQLite-базе |
| `DOWNLOADS_DIR` | `downloads` | директория временных файлов |
| `YTDLP_BIN` | `yt-dlp` | команда для запуска `yt-dlp` |
| `YTDLP_TIMEOUT_SECONDS` | `60` | timeout скачивания |
| `MAX_FILE_SIZE_MB` | `50` | лимит размера файла перед отправкой |
| `INSTAGRAM_COOKIES_PATH` | пусто | путь к `cookies.txt` при необходимости |
| `LOG_RETENTION_LIMIT` | `10000` | лимит строк логов |
| `STALE_FILE_MAX_AGE_HOURS` | `24` | возраст файлов для cleanup |

## Тесты

```powershell
uv sync --dev
uv run pytest
```

Дополнительно:

```powershell
uv run pytest .\tests\unit
uv run pytest .\tests\integration
```

## Лицензия

Проект распространяется под лицензией GNU Affero General Public License v3.0. См. [LICENSE](LICENSE).
