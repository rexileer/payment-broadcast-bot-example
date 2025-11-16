from django.db import models
from users.models import User, Channel

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)  # из YooKassa
    
    def __str__(self):
        return f"Платеж {self.id} от {self.user.telegram_id} на {self.amount} ({self.status})"

    
    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        
class PaymentMessage(models.Model):
    """
    Платежное сообщение
    Должно отправляться раз в 6 месяцев для каждого отдельного пользователя
    """
    text = models.TextField()

    def save(self, *args, **kwargs):
        if PaymentMessage.objects.exists():
            # Разрешаем обновлять только первую запись
            self.pk = PaymentMessage.objects.first().pk
        super().save(*args, **kwargs)

    def __str__(self):
        return "Платежное сообщение"
    
    class Meta:
        verbose_name = 'Платежное сообщение'
        verbose_name_plural = 'Платежное сообщение'

class PaymentItem(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='products', verbose_name='Канал', null=True, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    pay_period_months = models.PositiveSmallIntegerField(
        default=6,
        choices=[(i, f'{i} мес.') for i in range(1, 13)],
        verbose_name='Срок продления (в месяцах)'
    )

    def __str__(self):
        return f"{self.title} для {self.channel.name} ({self.pay_period_months} мес.)"

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
