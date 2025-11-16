import asyncio
import threading
import logging
from bot.aiogram_bot import bot
from aiogram.types import FSInputFile
from bot.services.user_service import get_all_users
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

logger = logging.getLogger('Posting')

loop = asyncio.new_event_loop()
loop_started = False

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

def ensure_loop_running():
    global loop_started
    if not loop_started:
        threading.Thread(target=start_loop, args=(loop,), daemon=True).start()
        loop_started = True

async def send_posting_to_users(posting_data):
    text = posting_data.get('text') or "Новая публикация!"
    media_type = posting_data.get('media_type')
    file_path = posting_data.get('file_path')
    users = await get_all_users()

    for user in users:
        await asyncio.sleep(0.05)
        await send_message(user.telegram_id, text, file_path, media_type)

async def send_message(user_id, text=None, file_path=None, media_type=None):
    try:
        if file_path:
            if media_type == "image":
                await bot.send_photo(user_id, FSInputFile(file_path), caption=text)
            elif media_type == "video":
                await bot.send_video(user_id, FSInputFile(file_path), caption=text)
            else:
                logger.warning(f"Неизвестный тип медиафайла: {media_type}")
        elif text:
            await bot.send_message(user_id, text)
        else:
            logger.warning("Пустая рассылка")
        logger.info(f"Сообщение отправлено {user_id}")
    except TelegramForbiddenError:
        logger.info(f"Пользователь {user_id} заблокировал бота.")
    except TelegramRetryAfter as e:
        logger.error(f"⏳ Лимит Telegram API. Ждём {e.retry_after} сек.")
        await asyncio.sleep(e.retry_after)
        await send_message(user_id, text, file_path, media_type)
    except Exception as e:
        logger.error(f"Ошибка отправки {user_id}: {e}")

def send_posting(posting_data):
    ensure_loop_running()
    try:
        asyncio.run_coroutine_threadsafe(send_posting_to_users(posting_data), loop)
    except Exception as e:
        logger.error(f"Ошибка запуска рассылки: {e}")
