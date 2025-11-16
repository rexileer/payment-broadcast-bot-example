from bot.services.get_chat_members_service import get_chat_members
from bot.services.channels_service import get_all_channels
import logging

logger = logging.getLogger(__name__)

async def update_all_channels_users():
    channels = await get_all_channels()

    if not channels:
        logger.warning("❗️Нет активных каналов для обработки.")
        return

    for channel in channels:
        logger.info(f"📡 Обрабатываем канал: {channel.name} ({channel.channel_id})")
        try:
            added_users, updated_subs = await get_chat_members(channel.channel_id)
            logger.info(
                f"✅ Готово для {channel.name}!\n"
                f"➕ Добавлено: {added_users}, 🔁 Обновлено: {updated_subs}"
            )
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке канала {channel.name}: {e}")
