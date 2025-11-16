from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PostingMessage
import requests
import os
from requests.exceptions import RequestException

@receiver(post_save, sender=PostingMessage)
def send_posting_on_create(sender, instance, created, **kwargs):
    from django.utils.timezone import now
    print(f"[{now()}] Signal triggered for PostingMessage. Created: {created}")
    if created:
        try:
            data = {
                "posting_id": instance.id,
                "text": instance.text,
                "media_type": instance.media_type,
                "file_path": instance.file.path if instance.file else None,
            }
            response = requests.post(
                "http://http_server:8000/send_posting",
                json=data,
                timeout=5
            )
            if response.status_code != 200:
                print(f"Ошибка при отправке запроса к боту: {response.text}")
        except Exception as e:
            print(f"Ошибка при отправке запроса к боту: {e}")
