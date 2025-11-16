from bot.config import bot
from bot.services.channels_service import get_channel_by_id
from bot.services.payment_message_service import get_payment_message
from bot.keyboards.inline.to_payment_kb import generate_payment_button
from aiogram.types import InlineKeyboardMarkup

async def send_payment_notification(user_id, subscription):
    # Получаем канал, на который истекла подписка
    channel = await get_channel_by_id(subscription.channel_id)
    
    # Создаем кнопку для оплаты
    payment_button = generate_payment_button(channel)
    
    # Создаем клавиатуру с кнопкой
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[payment_button]])
    
    # Формируем сообщение
    message = await get_payment_message(channel)

    # Отправляем сообщение с кнопкой
    await bot.send_message(user_id, message, reply_markup=keyboard)