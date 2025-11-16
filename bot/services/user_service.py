from users.models import User, Channel, UserChannelSubscription
from asgiref.sync import sync_to_async
from django.utils.timezone import now
from datetime import timedelta


@sync_to_async
def get_all_users():
    return list(User.objects.all())


@sync_to_async
def get_user(telegram_id):
    try:
        return User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        return None

@sync_to_async
def get_user_subscriptions(telegram_id):
    """Получает все подписки пользователя"""
    user = User.objects.get(telegram_id=telegram_id)
    return list(UserChannelSubscription.objects.select_related('channel').filter(user=user))

@sync_to_async
def add_user(telegram_id):
    user, created = User.objects.get_or_create(telegram_id=telegram_id)
    return user


@sync_to_async
def create_subscription(telegram_id, channel_id):
    user = User.objects.get(telegram_id=telegram_id)
    channel = Channel.objects.get(channel_id=channel_id)
    return UserChannelSubscription.objects.get_or_create(user=user, channel=channel)


@sync_to_async
def update_user_payment(telegram_id, channel_id):
    """Обновление подписки на 6 месяцев для конкретного канала"""
    user = User.objects.get(telegram_id=telegram_id)
    channel = Channel.objects.get(channel_id=channel_id)
    return UserChannelSubscription.objects.filter(user=user, channel=channel).update(
        is_paid=True,
        subscription_until=now() + timedelta(days=180),
        banned=False
    )


@sync_to_async
def ban_user_from_channel(telegram_id, channel_id):
    user = User.objects.get(telegram_id=telegram_id)
    channel = Channel.objects.get(channel_id=channel_id)
    return UserChannelSubscription.objects.filter(user=user, channel=channel).update(banned=True)


@sync_to_async
def unban_user_from_channel(telegram_id, channel_id):
    user = User.objects.get(telegram_id=telegram_id)
    channel = Channel.objects.get(channel_id=channel_id)
    return UserChannelSubscription.objects.filter(user=user, channel=channel).update(banned=False)
