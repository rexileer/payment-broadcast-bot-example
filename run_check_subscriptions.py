import os
import django
import asyncio
import logging
import gc  # Сборщик мусора
import psutil  # Для мониторинга памяти
from datetime import datetime, timedelta

# Устанавливаем тип сервиса для правильного выбора сессии в config.py
os.environ["SERVICE_TYPE"] = "checker"

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from bot.payment_sender import check_subscriptions
from bot.services.chat_member_updater import update_all_channels_users
from bot.config import bot_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('subscription_checker.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Настройка интервалов и задержек
CHECK_INTERVAL_SECONDS = 30 * 60  # каждые 30 минут (вместо 15)
SCAN_INTERVAL_SECONDS = 6 * 60 * 60  # каждые 6 часов 
last_check_time = None
last_scan_time = None

def log_memory_usage():
    """Логирует текущее использование памяти"""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    logger.info(f"Использование памяти: {mem_info.rss / 1024 / 1024:.2f} МБ")

async def init_bots():
    """Инициализация ботов при старте"""
    try:
        logger.info("Инициализация ботов для проверки подписок...")
        # Ждем 15 секунд перед инициализацией
        await asyncio.sleep(15)
        
        # Компактно выполняем инициализацию всех нужных компонентов
        await bot_manager.get_userbot()
        # Проверяем, что бот доступен
        if bot_manager.bot:
            await bot_manager.bot.get_me()
            logger.info("✅ Aiogram бот успешно проверен")
            
        logger.info("✅ Боты успешно инициализированы")
        # Форсируем сборку мусора
        gc.collect()
        log_memory_usage()
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации ботов: {e}", exc_info=True)
        raise

async def main():
    global last_check_time
    
    logger.info("🚀 Запуск сервиса проверки подписок")
    
    try:
        # Инициализируем ботов перед стартом
        await init_bots()
        
        while True:
            try:
                current_time = datetime.now()
                
                # Проверяем, прошло ли достаточно времени с последней проверки
                if last_check_time and (current_time - last_check_time).total_seconds() < CHECK_INTERVAL_SECONDS:
                    await asyncio.sleep(60)  # Спим минуту перед следующей проверкой
                    continue
                    
                logger.info("▶️ Запуск проверки подписок...")
                await check_subscriptions(logger=logger)
                logger.info("✅ Подписки проверены.")

                logger.info("▶️ Сканирование каналов...")
                await update_all_channels_users()
                logger.info("✅ Каналы просканированы.")
                
                last_check_time = current_time
                logger.info(f"⏰ Следующая проверка через {CHECK_INTERVAL_SECONDS/60} минут")
                
            except Exception as e:
                logger.error(f"💥 Ошибка в фоновом процессе: {e}", exc_info=True)
                await asyncio.sleep(60)  # При ошибке ждем минуту перед повторной попыткой
            else:
                await asyncio.sleep(60)  # Спим минуту перед следующей проверкой
    finally:
        # Закрываем соединения при выходе
        logger.info("Завершение работы сервиса проверки подписок")
        await bot_manager.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Сервис проверки подписок остановлен")
    except Exception as e:
        logger.critical(f"Критическая ошибка в сервисе проверки подписок: {e}", exc_info=True)
