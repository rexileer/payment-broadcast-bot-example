from django.contrib import admin
from .models import User, Channel, UserChannelSubscription


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'name', 'created_at')
    search_fields = ('telegram_id',)


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_id', 'link', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(UserChannelSubscription)
class UserChannelSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'channel', 'subscription_until', 'is_paid', 'banned')
    list_filter = ('is_paid', 'banned')
    search_fields = ('user__telegram_id', 'channel__name')
