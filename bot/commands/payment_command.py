from aiogram import Router, F
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import bot
from payment_config import config
from bot.services.payment_service import success_payment
from bot.services.channels_service import get_channel_by_id
from users.models import Channel
from payment.models import PaymentItem
from asgiref.sync import sync_to_async

import logging
logger = logging.getLogger(__name__)

router = Router()


class FSMPrompt(StatesGroup):
    choosing_channel = State()
    buying = State()


@sync_to_async
def get_active_channels():
    return list(Channel.objects.filter(is_active=True))


@router.callback_query(F.data.startswith("pay_channel_"))
async def buy_subscription_by_channel(callback, state: FSMContext):
    try:
        await callback.answer()
        channel_id = int(callback.data.split("_")[-1])
        await state.update_data(channel_id=channel_id)

        if config.provider_token.split(':')[1] == 'TEST':
            await callback.message.reply("Тестовая карта: 1111 1111 1111 1026, 12/22, CVC 000.")

        # Получаем продукт для этого канала
        try:
            item = await PaymentItem.objects.filter(channel_id=channel_id).afirst()
            if item:
                title = item.title
                description = item.description
                pay_period = item.pay_period_months
                price = config.price  # Можно добавить price в PaymentItem, если нужно разное
            else:
                title = "Подписка"
                description = "Оплата подписки на 6 месяцев"
                pay_period = 6
                price = config.price
        except Exception as e:
            logger.error(f"Error getting payment item: {e}")
            title = "Подписка"
            description = "Оплата подписки на 6 месяцев"
            pay_period = 6
            price = config.price

        prices = [LabeledPrice(label=f'Оплата подписки на {pay_period} мес.', amount=price)]
        await state.set_state(FSMPrompt.buying)

        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=title,
            description=description,
            payload=f'pay_channel_{channel_id}',
            provider_token=config.provider_token,
            currency="RUB",
            prices=prices,
        )
    except Exception as e:
        logger.error(f"Ошибка при выборе канала для оплаты: {e}")
        await callback.message.reply("Произошла ошибка при выборе канала!")


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    try:
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except Exception as e:
        logger.error(f"Ошибка при подтверждении оплаты: {e}")


@router.message(F.successful_payment)
async def process_successful_payment(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        channel_id = data.get("channel_id")
        amount = message.successful_payment.total_amount
        status = message.successful_payment.invoice_payload
        transaction_id = message.successful_payment.provider_payment_charge_id

        await message.reply(f"Оплата прошла успешно!")

        # Обновляем подписку
        await success_payment(
            telegram_id=message.from_user.id,
            amount=amount,
            status=status,
            transaction_id=transaction_id,
            channel_id=channel_id,
        )

        logger.info(f"Платёж успешен: {message.from_user.id} за канал {channel_id}")
        # Получаем Telegram ID канала
        channel = await get_channel_by_id(channel_id)
        telegram_channel_id = str(channel.channel_id)

        # Разбан пользователя
        try:
            await bot.unban_chat_member(telegram_channel_id, message.from_user.id)
            logger.info(f"Разбанили пользователя {message.from_user.id} в канале {telegram_channel_id} после оплаты")
        except Exception as e:
            logger.error(f"Ошибка при разбане пользователя {message.from_user.id} в канале {telegram_channel_id}: {e}")

        await message.reply(f"Подписка на канал {channel.name} успешно активирована! Вы можете пользоваться каналом.")
        try:
            channel_link = await bot.create_chat_invite_link(telegram_channel_id)
            await message.reply(f"Ссылка на канал: {channel_link.invite_link}")
        except Exception as e:
            logger.error(f"Ошибка при создании ссылки на канал {telegram_channel_id}: {e}")
            await message.reply("Не удалось создать ссылку на канал. Пожалуйста, свяжитесь с администратором.")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке успешного платежа: {e}")
        await message.reply("Произошла ошибка при обработке платежа!")
    finally:
        await state.clear()


@router.message(FSMPrompt.buying)
async def process_unsuccessful_payment(message: Message, state: FSMContext):
    await message.reply("Платеж не был завершён.")
    await state.clear()
