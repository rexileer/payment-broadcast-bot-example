import os
import asyncio
import time
import logging
from aiogram import Bot
from aiogram.client.bot import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from pyrogram import Client

logger = logging.getLogger(__name__)

# TELEGRAM
TOKEN = os.getenv('TELEGRAM_TOKEN')

# PAYMENT
PROVIDER_TOKEN = os.getenv('PROVIDER_TOKEN')
TEST_PROVIDER_TOKEN = os.getenv('TEST_PROVIDER_TOKEN')
CURRENCY = os.getenv('СURRENCY')
PRICE = os.getenv('PRICE')

# API USERBOT
API_HASH = os.getenv('API_HASH')
API_ID = os.getenv('API_ID')

# Определяем тип сервиса из переменной окружения, по умолчанию 'bot'
SERVICE_TYPE = os.getenv('SERVICE_TYPE', 'bot')
logger.info(f"Запуск сервиса типа: {SERVICE_TYPE}")

# Выбираем session_file в зависимости от типа сервиса
SESSION_FILES = {
    'bot': 's1_bot',
    'checker': 's1_checker',
    'fallback': 's1_fallback'
}

# Путь к файлу сессии для текущего сервиса
CURRENT_SESSION_FILE = SESSION_FILES.get(SERVICE_TYPE, 's1_bot')
SESSION_PATH = os.path.join(os.getcwd(), "bot", CURRENT_SESSION_FILE)
logger.info(f"Используется файл сессии: {SESSION_PATH}")

class BotManager:
    _instance = None
    _bot = None
    _userbot = None
    _session = None
    _lock = asyncio.Lock()
    _last_close_time = 0
    _close_cooldown = 30  # секунды между закрытиями

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BotManager, cls).__new__(cls)
            cls._session = AiohttpSession()
            # aiogram-бот инициализируем для сервисов, которым он нужен (bot, http, checker)
            if SERVICE_TYPE in ['bot', 'http', 'checker']:
                logger.info("Инициализация aiogram-бота")
                cls._bot = Bot(token=TOKEN, session=cls._session, default=DefaultBotProperties(parse_mode='HTML'))
            else:
                logger.info(f"Для сервиса {SERVICE_TYPE} aiogram-бот не инициализируется")
        return cls._instance

    @property
    def bot(self):
        if not self._bot:
            logger.warning("Попытка использовать aiogram-бота в сервисе, где он не инициализирован")
        return self._bot

    async def get_userbot(self):
        """Получаем userbot (Pyrogram Client) для текущего сервиса с соответствующим session_file"""
        async with self._lock:
            if self._userbot is None:
                try:
                    # Используем session_file для текущего сервиса
                    logger.info(f"Инициализация Pyrogram Client с сессией {SESSION_PATH}")
                    
                    # Создаем директорию для сессии, если её нет
                    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)
                    
                    self._userbot = Client(SESSION_PATH, API_ID, API_HASH)
                    await self._userbot.start()
                    logger.info(f"✅ Userbot успешно инициализирован (сессия: {CURRENT_SESSION_FILE})")
                except Exception as e:
                    logger.error(f"❌ Ошибка инициализации юзербота: {e}")
                    raise
            return self._userbot

    async def close(self):
        current_time = time.time()
        if current_time - self._last_close_time < self._close_cooldown:
            logger.warning("Пропускаем закрытие ботов из-за cooldown")
            return

        try:
            closed_something = False
            if self._bot:
                logger.info("Закрываем aiogram-бота")
                await self._bot.close()
                closed_something = True
            if self._userbot:
                logger.info("Закрываем Pyrogram Client")
                await self._userbot.stop()
                closed_something = True
            if closed_something:
                self._last_close_time = current_time
                logger.info("✅ Боты успешно закрыты")
        except Exception as e:
            logger.error(f"❌ Ошибка при закрытии ботов: {e}")

# Create singleton instance
bot_manager = BotManager()
bot = bot_manager.bot
