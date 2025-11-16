# from aiogram import Router
# from aiogram.types import Message
# from aiogram.filters import Command
# from services.get_chat_members_service import get_chat_members
# from services.channels_service import get_all_channels
# from users.models import Channel

# import logging
# logger = logging.getLogger(__name__)

# router = Router()

# @router.message(Command('all_members'))
# async def cmd_all_members(message: Message):
#     channels = await get_all_channels()

#     if not channels:
#         await message.reply("❗️Нет активных каналов для обработки.")
#         return

#     for channel in channels:
#         await message.reply(f"📡 Обрабатываем канал: {channel.name} ({channel.channel_id})")
#         try:
#             added_users, updated_subs = await get_chat_members(channel.channel_id)
#             await message.reply(
#                 f"✅ Готово для {channel.name}!\n"
#                 f"➕ Добавлено новых пользователей: {added_users}\n"
#                 f"🔁 Обновлено подписок: {updated_subs}"
#             )
#         except Exception as e:
#             logger.error(f"Ошибка при обработке канала {channel.channel_id}: {e}")
#             await message.reply(f"❌ Ошибка при обработке канала {channel.name}: {e}")
