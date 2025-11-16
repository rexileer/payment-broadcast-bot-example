import os
import sys

# Устанавливаем тип сервиса для правильного выбора сессии в config.py
os.environ["SERVICE_TYPE"] = "bot"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.update({'DJANGO_ALLOW_ASYNC_UNSAFE': "true"})

import django
django.setup()

import asyncio
from aiogram import Dispatcher
from commands import start_command, payment_command, chat_members_command
from bot.config import bot_manager, bot

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot_logs.log', mode='a')  # Запись логов в файл 'bot_logs.log'
    ]
)

logger = logging.getLogger("TelegramBot")

async def init_bots():
    """Инициализация ботов при старте"""
    try:
        logger.info("Инициализация Pyrogram Client...")
        # Инициализируем юзербота с сессией для основного бота
        await bot_manager.get_userbot()
        logger.info("✅ Боты успешно инициализированы")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации ботов: {e}", exc_info=True)
        raise

async def main():
    logger.info("🚀 Запуск основного Telegram бота")
    
    try:
        # Инициализируем ботов перед стартом
        await init_bots()
        
        dp = Dispatcher()
        
        dp.include_routers(
            start_command.router,
            payment_command.router,
            # chat_members_command.router,
        )
        
        logger.info("✅ Диспетчер настроен, запускаем поллинг")
        
        await asyncio.gather(
            bot.delete_webhook(drop_pending_updates=True),
            dp.start_polling(bot, skip_updates=False),
        )
        
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
    finally:
        logger.info("Завершение работы бота")
        await bot_manager.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
    except Exception as e:
        logger.critical(f"Критическая ошибка в боте: {e}", exc_info=True)