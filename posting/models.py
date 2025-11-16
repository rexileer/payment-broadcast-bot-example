from django.db import models
from django.utils.timezone import now


class PostingMessage(models.Model):
    text = models.TextField("Текст сообщения", blank=True, null=True)
    file = models.FileField("Медиафайл", upload_to="media/", blank=True, null=True)
    media_type = models.CharField(
        "Тип медиафайла",
        max_length=10,
        choices=[("image", "Изображение"), ("video", "Видео")],
        blank=True,
        null=True,
    )
    send_time = models.DateTimeField("Время отправки", default=now)

    def __str__(self):
        return f"Публикация {self.id}"
    
    class Meta:
        verbose_name = 'Публикация'
        verbose_name_plural = 'Публикации'

class StartCommandResponse(models.Model):
    text = models.TextField()

    def save(self, *args, **kwargs):
        if StartCommandResponse.objects.exists():
            # Разрешаем обновлять только первую запись
            self.pk = StartCommandResponse.objects.first().pk
        super().save(*args, **kwargs)

    def __str__(self):
        return "Приветственное сообщение"
    
    class Meta:
        verbose_name = 'Приветственное сообщение'
        verbose_name_plural = 'Приветственное сообщение'

class FallbackNotificationMessage(models.Model):
    text = models.TextField()

    def save(self, *args, **kwargs):
        if FallbackNotificationMessage.objects.exists():
            self.pk = FallbackNotificationMessage.objects.first().pk
        super().save(*args, **kwargs)

    def __str__(self):
        return "Текст для fallback-уведомления"

    class Meta:
        verbose_name = 'Fallback-уведомление'
        verbose_name_plural = 'Fallback-уведомление'