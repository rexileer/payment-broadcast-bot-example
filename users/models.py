from django.db import models
from django.utils.timezone import now
from datetime import timedelta

class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    name = models.CharField(default="", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Пользователь telegram'
        verbose_name_plural = 'Пользователи telegram'
        
class Channel(models.Model):
    name = models.CharField(max_length=255, default="")
    channel_id = models.BigIntegerField(unique=True)
    link = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Канал'
        verbose_name_plural = 'Каналы'
        
        
class UserChannelSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='subscriptions')
    is_paid = models.BooleanField(default=False)
    banned = models.BooleanField(default=False)
    
    def default_subscription():
        return now() + timedelta(days=180)
        
    subscription_until = models.DateTimeField(default=default_subscription, blank=True)

    class Meta:
        unique_together = ('user', 'channel')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f"{self.user.name} -> {self.channel.name}"
