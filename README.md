# Payment Broadcast Platform

Платформа объединяет Django-бэкенд, aiogram-бота и Pyrogram userbot для управления платными Telegram-подписками, отправки уведомлений и контентных рассылок. Проект демонстрирует полный цикл: от продажи подписки через встроенные платежи Telegram до автоматического контроля доступа в каналы и отправки fallback-сообщений, если основной бот недоступен пользователю.

## Highlights
- Полностью асинхронные сценарии в боте: aiogram + Pyrogram + Django ORM через `async`/`sync_to_async`.
- Много сервисов в одном репозитории: веб-приложение, бот, HTTP-триггер рассылок и воркер проверки подписок.
- Встроенный платежный флоу (YooKassa / Telegram Payments) с продуктами, периодами продления и автоматическим управлением подписками (`PaymentItem`, `UserChannelSubscription`).
- Дополнительный userbot с собственными сессиями для fallback-уведомлений и обхода ограничений Telegram.
- Отдельное Django-приложение `posting` для хранения сообщений, fallback-текстов и стартовых ответов, что упрощает редактирование контента без перепаковки бота.

## Архитектура
```
┌────────────┐   webhooks / REST   ┌──────────────┐
│  aiogram   │◀────────────────────│  Django API  │
│  bot/tg    │                     │   (core)     │
└────┬───────┘                     └────┬─────────┘
     │                                  │
     │Pyrogram userbot (fallback)       │PostgreSQL
     ▼                                  ▼
┌───────────────┐                ┌──────────────┐
│subscription   │⟳ periodic job  │ payment/post │
│checker        │───────────────▶│ users apps   │
└───────────────┘                └──────────────┘
        ▲
        │HTTP POST /send_posting
┌───────┴────────┐
│http_server +   │
│bot/post_sender │
└────────────────┘
```

### Основные компоненты
- **`core/`** — конфигурация Django 5.1 (PostgreSQL, `.env`, RU локаль).
- **`users/`** — пользователи Telegram, каналы, подписки и их статусы `is_paid`/`banned`.
- **`payment/`** — модели платежей, продукты (`PaymentItem`), тексты уведомлений (`PaymentMessage`).
- **`posting/`** — текст приветствия (`StartCommandResponse`), fallback-уведомления и очередь сообщений для массовых рассылок.
- **`bot/`** — aiogram-команды (`start`, `pay`), платежная FSM, сервисы отправки уведомлений, интеграция с Pyrogram userbot и HTTP-сервер для запуска рассылок.
- **`run_check_subscriptions.py`** — отдельный воркер, который циклически проверяет сроки подписок и синхронизирует участников каналов.

## Сервисная топология (docker-compose)
| Сервис | Команда | Назначение |
| --- | --- | --- |
| `web` | `python manage.py runserver` | Панель администратора, API, фоновые Django-задачи. |
| `tg_bot` | `python bot/tg_bot.py` | Aiogram 3 бот с командами `/start` и оплатой подписок. |
| `http_server` | `python bot/http_server.py` | HTTP endpoint `POST /send_posting` → триггерит `bot/post_sender.py`. |
| `subscription_checker` | `python run_check_subscriptions.py` | Проверяет подписки каждые 30 минут, синхронизирует участников Pyrogram userbot’ом. |
| `db` | `postgres:13` | Основная БД. |

Каждый сервис получает собственный `SERVICE_TYPE`, чтобы `bot.config` подхватил корректный Pyrogram session file (`s1_bot`, `s1_checker`, `s1_fallback`) и не делил сессии между контейнерами.

## Telegram и платежный стек
- **Aiogram 3.19**: FSM для выбора канала и оплаты, inline-инвойсы (`send_invoice`), `PreCheckoutQuery`.
- **Pyrogram 2.x**: отдельный userbot для fallback-сообщений и полного перечня участников канала (`get_chat_members`). Переопределяется `pyrogram.utils.get_peer_type`, чтобы работать с channel-id формата `-100`.
- **Платежи**: `bot/payment_config.py` формирует payload для провайдера (YooKassa) и чек (`provider_data`). После успешной оплаты `bot/services/payment_service.success_payment` продлевает подписку на базовый период из `PaymentItem`.
- **Уведомления**: `send_payment_notification` использует `PaymentMessage` + inline-кнопку `pay_channel_{channel.id}`, бот банит/разбанивает участников, а `PaymentMessageService.send_message_with_fallback` подключает userbot в случае `TelegramForbiddenError`.

## Основные доменные сценарии
### Продажа и продление подписки
1. Пользователь выбирает канал (callback `pay_channel_{id}`) и получает invoice.
2. `process_successful_payment` фиксирует сумму/статус, вызывает `success_payment`, снимает бан и создает пригласительную ссылку.
3. `Payment` + `PaymentItem` позволяют хранить историю транзакций и периоды (по умолчанию 6 месяцев).

### Контроль подписок
- `run_check_subscriptions.py` каждые 30 минут вызывает `check_subscriptions`.
- Истекшие платежи получают уведомление → статус `is_paid=False`. Если пользователь не реагирует 24 часа, бот банит его в канале.
- Дополнительно запускается `update_all_channels_users()`, который синхронизирует участников из Pyrogram в Django (`UserChannelSubscription`).

### Рассылки и fallback
- Контент хранится в `PostingMessage`. `bot/http_server.py` слушает `/send_posting` и прокидывает payload в `bot/post_sender.send_posting`.
- `post_sender` держит собственный event loop, рассылка идет с контролем API-лимитов (повтор при `TelegramRetryAfter`), игнорирует пользователей, заблокировавших бота.
- `FallbackNotificationMessage` задаёт дефолтный текст, которым userbot достучится до пользователя, если основной бот заблокирован.

## Технологии
- Python 3.13, Django 5.1, Aiogram 3, Pyrogram 2, PostgreSQL, YooKassa SDK.
- `asgiref`, `aiohttp`, `psutil`, `python-dotenv` для конфигурации и мониторинга.
- Dockerfile и docker-compose для изолированного запуска.

## Подготовка окружения
1. **Зависимости**: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
2. **База данных**: PostgreSQL 13+. Создайте базу/пользователя и пропишите параметры в `.env`.
3. **Переменные окружения** (пример `.env`):
   ```
   DJANGO_SECRET_KEY=...
   DEBUG=True
   POSTGRES_DB=payment_bot
   POSTGRES_USER=payment_bot
   POSTGRES_PASSWORD=...
   POSTGRES_HOST=localhost
   TELEGRAM_TOKEN=...
   API_ID=...
   API_HASH=...
   PROVIDER_TOKEN=381764678:TEST:...      # Telegram/YooKassa
   TEST_PROVIDER_TOKEN=...
   CURRENCY=RUB
   PRICE=10000                            # minor units, напр. 100 rub = 10000
   TZ=Europe/Moscow
   CONTAINER_NAME=paymentbot
   NETWORK_NAME=paymentbot-net
   BOT_HTTP_PORT=8000
   ```
   > Переменная `СURRENCY` в коде записана кириллицей — добавьте обе (`CURRENCY` и `СURRENCY`) в `.env`, чтобы избежать путаницы.
4. **Миграции и суперпользователь**:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
5. **Pyrogram session**: перед запуском сервисов создайте файлы сессий.
   ```bash
   python create_session.py --type bot
   python create_session.py --type checker
   ```

## Запуск в разработки
В отдельных терминалах:
```bash
python manage.py runserver 0.0.0.0:8000
python bot/tg_bot.py                       # основной бот
python bot/http_server.py                  # HTTP endpoint для рассылок
python run_check_subscriptions.py          # воркер проверки подписок
```
Для ручного теста рассылки:
```bash
curl -X POST http://localhost:8001/send_posting \
     -H "Content-Type: application/json" \
     -d '{"text": "Привет подписчикам!", "media_type": null, "file_path": null}'
```

## Запуск через Docker Compose
```bash
docker compose --env-file .env up --build
```
Логи пишутся в файлы (`bot_logs.log`, `subscription_checker.log`, `http_server.log`) и stdout контейнеров. Volumes `bot_session`/`checker_session` сохраняют Pyrogram-сессии между рестартами.

## Тестирование
- Модульные тесты запускаются стандартно: `python manage.py test`.
- Для проверки платежного сценария используйте тестовые карты Telegram: `1111 1111 1111 1026, 12/22, CVC 000` — бот автоматически отправит подсказку, если провайдерский токен тестовый.

## Полезные ссылки
- `bot/payment_sender.py` — бизнес-логика продления/бана.
- `bot/services/payment_message_service.py` — fallback через userbot, повторные попытки с `FloodWait`.
- `bot/services/get_chat_members_service.py` — прямой импорт участников канала в БД.
- `bot/post_sender.py` + `bot/http_server.py` — ручные рассылки через HTTP.

Проект можно расширять: добавлять celery/Redis для фоновых задач, встраивать веб-интерфейс для запуска рассылок или подключать второй платежный провайдер. README описывает текущее состояние и основные решения, чтобы быстро погрузиться в кодовую базу.