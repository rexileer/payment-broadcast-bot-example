from payment.models import PaymentMessage
from aiogram.exceptions import TelegramForbiddenError
from bot.config import bot_manager
from posting.models import FallbackNotificationMessage
import logging
from pyrogram.errors import PeerIdInvalid, UsernameInvalid, FloodWait
import asyncio
from users.models import User as UserModel  # Импортируем модель пользователя из Django
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


async def get_payment_message(channel) -> str:
    msg = await PaymentMessage.objects.afirst()
    return msg.text if msg else f"Ваша подписка на канал {channel.name} истекла. Пожалуйста, оплатите подписку для продолжения."


async def send_message_with_fallback(user_id: int, text: str):
    logger.warning(f"Основной бот не может отправить сообщение пользователю {user_id}, пробуем юзербота")
    # Получаем сообщение из базы
    fallback_msg = await FallbackNotificationMessage.objects.afirst()
    if not fallback_msg:
        logger.warning("Нет fallback-сообщения в базе")
        fallback_msg = FallbackNotificationMessage(text="Пожалуйста, оплатите подписку через бота для доступа к группе.")

    # Пробуем получить username пользователя из базы данных
    username = None
    try:
        user = await UserModel.objects.filter(telegram_id=user_id).afirst()
        if user and user.name:
            # Если имя без пробелов и длиннее 3 символов, это может быть username
            if ' ' not in user.name and len(user.name) > 3:
                # Убираем @ если он есть в начале
                username = user.name.lstrip('@').strip()
            
        if username:
            logger.info(f"Нашли возможный username для {user_id}: {username}")
    except Exception as e:
        logger.warning(f"Ошибка при получении username из базы для {user_id}: {e}")

    try:
        # Используем userbot из текущего контейнера/сервиса
        logger.info(f"Инициализация userbot для fallback сообщения пользователю {user_id}")
        userbot = await bot_manager.get_userbot()
        
        try:
            # Пытаемся "познакомиться" с пользователем перед отправкой сообщения
            logger.info(f"Пытаемся получить информацию о пользователе {user_id}")
            user_found = False
            
            # Попытка 1: Ищем по ID в общих чатах
            try:
                common_chats = await userbot.get_common_chats(user_id)
                logger.info(f"Найдено общих чатов с пользователем {user_id}: {len(common_chats)}")
                if common_chats:
                    user_found = True
            except Exception as e:
                logger.warning(f"Не удалось найти общие чаты с {user_id}: {e}")
            
            # Попытка 2: Ищем по диалогам, если не нашли в общих чатах
            if not user_found:
                try:
                    logger.info(f"Пробуем найти пользователя {user_id} в диалогах")
                    async for dialog in userbot.get_dialogs(limit=100):
                        if dialog.chat.type in ["group", "supergroup", "channel"]:
                            try:
                                member = await userbot.get_chat_member(dialog.chat.id, user_id)
                                logger.info(f"Нашли пользователя {user_id} в чате {dialog.chat.title}")
                                user_found = True
                                break
                            except:
                                continue
                except Exception as e:
                    logger.warning(f"Ошибка при поиске в диалогах: {e}")
            
            # Попытка 3: Если есть username, пробуем по нему
            if not user_found and username:
                try:
                    logger.info(f"Пробуем найти пользователя по username @{username}")
                    user_info = await userbot.get_users(username)
                    logger.info(f"Успешно нашли пользователя по username @{username}: {user_info.first_name}")
                    user_found = True
                    # Обновляем user_id на найденный через username
                    user_id = user_info.id
                except Exception as e:
                    logger.warning(f"Не удалось найти пользователя по username @{username}: {e}")
            
            # Попытка 4: Прямой запрос информации о пользователе
            if not user_found:
                try:
                    user_info = await userbot.get_users(user_id)
                    logger.info(f"Успешно получена информация о пользователе {user_id}: {user_info.first_name}")
                    user_found = True
                except Exception as e:
                    logger.warning(f"Не удалось получить информацию о пользователе {user_id}: {e}")
            
        except Exception as e:
            logger.warning(f"Ошибка при попытке найти пользователя {user_id}: {e}")
            # Продолжаем попытку отправки сообщения даже если не удалось получить информацию
        
        # Пробуем отправить сообщение с повторными попытками
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                # Если нашли username и не смогли найти по ID, пробуем по username
                if not user_found and username:
                    logger.info(f"Отправляем fallback по username @{username} (попытка {attempt})")
                    await userbot.send_message(chat_id=f"@{username}", text=fallback_msg.text)
                    logger.info(f"Fallback-сообщение отправлено через username @{username}")
                    return True
                else:
                    logger.info(f"Отправляем fallback-сообщение через userbot пользователю {user_id} (попытка {attempt})")
                    await userbot.send_message(chat_id=user_id, text=fallback_msg.text)
                    logger.info(f"Fallback-сообщение отправлено пользователю {user_id}")
                    return True
            except FloodWait as e:
                logger.warning(f"FloodWait на {e.value} секунд при отправке сообщения {user_id}")
                if attempt < max_retries:
                    await asyncio.sleep(e.value + 1)
            except (PeerIdInvalid, UsernameInvalid):
                if username and attempt == 1:  # Если есть username и это первая попытка с ID
                    logger.warning(f"ID {user_id} не найден, пробуем отправить по username @{username}")
                    continue  # Попробуем через username в следующей итерации
                logger.error(f"Невозможно отправить сообщение пользователю {user_id}: пользователь не найден")
                return False
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Ошибка при отправке сообщения пользователю {user_id} (попытка {attempt}): {e}")
                    await asyncio.sleep(2)
                else:
                    raise
        
        return False
    except Exception as e:
        logger.error(f"Ошибка при отправке fallback-сообщения через юзербота пользователю {user_id}: {e}", exc_info=True)
        return False