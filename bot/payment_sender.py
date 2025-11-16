from django.utils.timezone import now, timedelta
from bot.config import bot
from bot.services.payment_message_service import send_message_with_fallback
from bot.services.channels_service import get_all_channels, get_channel_subscriptions
from bot.services.payment_notification import send_payment_notification
from asgiref.sync import sync_to_async

import logging
logger = logging.getLogger(__name__)


async def check_subscriptions(logger=logger):
    """Проверяет подписки на все каналы, уведомляет и банит при просрочке"""

    channels = await get_all_channels()

    for channel in channels:
        group_id = str(channel.channel_id)

        # Все подписки на канал (сервис, sync_to_async)
        subscriptions = await sync_to_async(get_channel_subscriptions)(channel)

        for subscription in subscriptions:
            if subscription.subscription_until <= now():

                user = subscription.user
                telegram_id = user.telegram_id

                if subscription.banned:
                    continue  # уже обработан

                time_diff = now() - subscription.subscription_until

                # Если прошло более 1 суток с окончания подписки — баним
                if time_diff > timedelta(days=1):
                    try:
                        await bot.ban_chat_member(group_id, telegram_id)
                        # await bot.unban_chat_member(group_id, telegram_id)
                        subscription.banned = True
                        subscription.is_paid = False
                        await sync_to_async(subscription.save)()
                        logger.info(f"Забанили пользователя {telegram_id} за неуплату в канале {channel.name}")
                    except Exception as e:
                        logger.error(f"Ошибка при бане {telegram_id} в канале {channel.name}: {e}")

                elif subscription.is_paid:
                    try:
                        # Отправляем уведомление с кнопкой "Оплатить"
                        await send_payment_notification(telegram_id, subscription)

                        # Обновляем статус подписки
                        subscription.is_paid = False
                        await sync_to_async(subscription.save)()

                        logger.info(f"Оповестили пользователя {telegram_id} о платеже за канал {channel.name}")

                    except Exception as e:
                        logger.error(f"Ошибка при уведомлении {telegram_id} за канал {channel.name}: {e}. Вероятно, пользователь не подписан на бота")

                        # Пробуем fallback-уведомление
                        try:
                            await send_message_with_fallback(telegram_id, f"Уведомление о платеже за канал: {channel.name}")
                            subscription.is_paid = False
                            await sync_to_async(subscription.save)()
                            logger.info(f"Fallback-сообщение отправлено, is_paid установлен в False для {telegram_id}")                      
                        except Exception as fallback_error:
                            logger.error(f"Ошибка при отправке fallback-сообщения {telegram_id} в канале {channel.name}: {fallback_error}")

                            # Баним, если fallback тоже не прошёл
                            try:
                                await bot.ban_chat_member(group_id, telegram_id)
                                # await bot.unban_chat_member(group_id, telegram_id)
                                subscription.banned = True
                                subscription.is_paid = False
                                await sync_to_async(subscription.save)()
                                logger.info(f"Забанили пользователя {telegram_id} за неуплату в канале {channel.name}")
                            except Exception as ban_error:
                                logger.error(f"Ошибка при бане {telegram_id} в канале {channel.name}: {ban_error}")
