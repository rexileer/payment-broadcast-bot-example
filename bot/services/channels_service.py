from users.models import Channel, UserChannelSubscription
from asgiref.sync import sync_to_async

@sync_to_async
def get_all_channels():
    return list(Channel.objects.filter(is_active=True))


def get_channel_subscriptions(channel):
    """Получает все подписки на канал с подгрузкой пользователя"""
    return list(UserChannelSubscription.objects.select_related('user').filter(channel=channel))

@sync_to_async
def get_channel_by_id(id):
    return Channel.objects.get(id=id)

def get_channel_link(id):
    return Channel.objects.get(id=id).link