from posting.models import StartCommandResponse
from users.models import User

async def get_start_message():
    msg = await StartCommandResponse.objects.afirst()
    return msg.text if msg else "Привет! Добро пожаловать в бота."

async def add_user(telegram_id, name):
    if User.objects.filter(telegram_id=telegram_id).exists():
        return
    await User.objects.acreate(telegram_id=telegram_id, name=name)