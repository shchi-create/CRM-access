# CRM Access API

Готовыи к деплою backend на FastAPI и aiogram для работы с Google Sheets. Приложение предоставляет HTTP API, совместимыи по поведению с Apps Script, и Telegram-бота с теми же сценариями.

## Возможности

- POST API с действиями `search` и `get_trip`.
- Telegram-бот с командами `/search` и `/get_trip`.
- Доступ только по API ключу и ACL списку user_id.
- In-memory кеш с TTL и ограничением количества строк.
- Локальные unit тесты.

## Структура проекта

```
app/
  main.py
  bot.py
  api.py
  sheets_client.py
  cache.py
  search.py
  security.py
  config.py
  logging_setup.py
  models.py
tests/
  test_search.py
  test_get_trip.py
Dockerfile
railway.toml
requirements.txt
README.md
.env.example
```

## Быстрыи запуск локально

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' .env.example | xargs)
uvicorn app.main:app --reload
```

## Переменные окружения

- `GOOGLE_SERVICE_ACCOUNT_JSON` — JSON ключ сервисного аккаунта как строка.
- `SPREADSHEET_ID` — ID таблицы.
- `API_KEY` — ключ доступа к API.
- `X_API_KEY_HEADER_NAME` — имя заголовка с ключом, по умолчанию `x-api-key`.
- `ALLOWED_USER_IDS` — CSV список Telegram user_id.
- `TELEGRAM_BOT_TOKEN` — токен бота.
- `CACHE_TTL` — TTL кеша в секундах.
- `RATE_LIMIT_PER_MIN` — лимит запросов в минуту.
- `MAX_SEARCH_RESULTS` — максимальное число результатов поиска.
- `MAX_SHEET_ROWS` — ограничение строк при чтении листов (по умолчанию 50000).
- `ENV` — `production` или `dev`.
- `SENTRY_DSN` — опционально, если используете Sentry.

## Примеры curl

Поиск:

```bash
curl -X POST https://<your-host>/api \
  -H "Content-Type: application/json" \
  -H "x-api-key: <API_KEY>" \
  -H "x-user-id: <USER_ID>" \
  -d '{"action":"search","surname":"Ivanov"}'
```

Get trip:

```bash
curl -X POST https://<your-host>/api \
  -H "Content-Type: application/json" \
  -H "x-api-key: <API_KEY>" \
  -H "x-user-id: <USER_ID>" \
  -d '{"action":"get_trip","trip_id":"TRIP1234"}'
```

## Настроика Google Service Account

1. Создаи сервисныи аккаунт в GCP.
2. Создаи JSON ключ и сохраните его локально, не добавляите в репозитории.
3. Разрешите доступ на чтение таблицы: поделитесь Google Sheets с email сервисного аккаунта.
4. Используите scope только `https://www.googleapis.com/auth/spreadsheets.readonly`.
5. В `GOOGLE_SERVICE_ACCOUNT_JSON` передаи JSON как строку.

## Telegram user_id

- Откроите бота `@userinfobot` и отправьте `/start`, он покажет ваш user_id.

## Railway

- Добавьте все переменные окружения из `.env.example` в настроиках проекта.
- Railway обеспечивает HTTPS в продакшене.

## Безопасность

- Не храните ключи в репозитории.
- Используите минимальные права (read-only) для сервисного аккаунта.
- Регулярно обновляите ключи и токены.
- Не логируите персональные данные.
- Для HTTP обязательно передавать `x-user-id` из списка `ALLOWED_USER_IDS`.

## Ограничения

- Кеш хранит только нужные колонки.
- Если лист содержит более 100000 строк, будут использованы только первые 50000 строк.

## Тестирование

```bash
pytest
```
