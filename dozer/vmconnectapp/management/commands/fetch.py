''' fetch.py '''
from django.core.management.base import BaseCommand
from vmconnectapp.vconnect import fetch_vcenter_data, save_vms_to_db, sync_pretty_names_with_db

class Command(BaseCommand):
    help = 'Получение данных из vCenter, сохранение в БД и поиск новых ОС.'

    def handle(self, *args, **kwargs):
        vms = fetch_vcenter_data()
        save_vms_to_db(vms)
        sync_pretty_names_with_db(vms)
