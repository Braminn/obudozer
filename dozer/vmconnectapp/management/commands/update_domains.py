from django.core.management.base import BaseCommand
from vmconnectapp.models import save_domains_to_db  # Импортируем функцию из models.py

class Command(BaseCommand):
    help = 'Парсит конфигурацию Nginx и сохраняет домены в БД'

    def handle(self, *args, **kwargs):
        save_domains_to_db()  # Вызываем функцию сохранения доменов
        self.stdout.write(self.style.SUCCESS('Домены успешно сохранены в базу данных'))
