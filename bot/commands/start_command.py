from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from services.user_service import get_user_subscriptions
from services.start_service import get_start_message, add_user
from services.payment_notification import send_payment_notification

import logging
logger = logging.getLogger(__name__)

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    logger.info(f"Received /start command from {message.from_user.id}")
    try:
        name = message.from_user.username or ""
        await add_user(message.from_user.id, name)
    except Exception as e:
        logger.error(f"Error adding user: {e}")
    try:
        text = await get_start_message()
    except Exception as e:
        logger.error(f"Error getting start message: {e}")
        text = "Добро пожаловать в бота"
    await message.answer(text, reply_markup=None)
    
    user_id = message.from_user.id
    subscriptions = await get_user_subscriptions(user_id)  # Получаем подписки пользователя

    # Проверяем, есть ли истекшие подписки
    expired_subscriptions = [sub for sub in subscriptions if not sub.is_paid]
    
    if expired_subscriptions:
        # Если есть истекшие подписки, отправляем уведомление для каждого канала
        for subscription in expired_subscriptions:
            await send_payment_notification(user_id, subscription)
    