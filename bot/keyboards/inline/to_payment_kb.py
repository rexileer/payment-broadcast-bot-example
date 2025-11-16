from aiogram.types import InlineKeyboardButton


def generate_payment_button(channel):
    return InlineKeyboardButton(
        text=f"Оплатить подписку на {channel.name}",
        callback_data=f"pay_channel_{channel.id}"
    )