from django.contrib import admin
from .models import PaymentMessage, Payment, PaymentItem

admin.site.site_header = "Редактирование"

@admin.register(PaymentMessage)
class PaymentMessageAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not PaymentMessage.objects.exists()  # Разрешаем добавлять, только если нет записей

    def has_delete_permission(self, request, obj=None):
        return False  # Запрещаем удаление

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'status', 'created_at', 'transaction_id')
    search_fields = ('user__telegram_id', 'transaction_id')
    list_filter = ('status',)
    
@admin.register(PaymentItem)
class PaymentItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'channel', 'pay_period_months', 'description')
    list_filter = ('channel', 'pay_period_months')
    search_fields = ('title', 'description')