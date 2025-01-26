''' domains.py '''
from django.core.management.base import BaseCommand
from vmconnectapp.models import NginxDomain, NginxConfig
from domainsapp.services import analyze_all_configs, print_server_info

class Command(BaseCommand):
    help = 'Парсит конфигурацию Nginx и сохраняет домены в БД'

    def handle(self, *args, **kwargs):
        def save_nginx_data_to_db(nginx_data):
            for domain_name, configs in nginx_data.items():
                domain, _ = NginxDomain.objects.get_or_create(domain_name=domain_name)
                for config in configs:
                    # Добавляем флаг waf, если в ip_addresses есть IP 192.168.124.200
                    waf = False
                    ip_addresses = [ip_tuple[0] for ip_tuple in config.get("ip_addresses", [])]  # Извлекаем все IP-адреса
                    if '192.168.124.200' in ip_addresses:  # Проверяем, есть ли нужный IP
                        waf = True

                    # Сохраняем конфигурацию с флагом waf
                    NginxConfig.objects.create(
                        domain=domain,
                        listen_ports=config.get("listen", []),
                        ip_addresses=config.get("ip_addresses", []),
                        waf=waf  # Добавляем значение waf
                    )

        print('Updating...')
        # Удаляем все записи из таблиц
        NginxDomain.objects.all().delete()
        print("Все записи удалены из таблицы NginxDomain.")
        NginxConfig.objects.all().delete()
        print("Все записи удалены из таблицы NginxConfig.")


        CONFIG_DIRECTORY = "/home/stegancevva@admlr.loc/Doc/Python/nginx-configurations-obu/"
        CONFIG_DIRECTORY2 = "/home/stegancevva@admlr.loc/Doc/Python/nginx-configurations-rsnet/"

        print('Обновляем OBU')
        nginx_data = analyze_all_configs(CONFIG_DIRECTORY)
        print_server_info(nginx_data)
        save_nginx_data_to_db(nginx_data)

        print('Обновляем RSNET')
        nginx_data2 = analyze_all_configs(CONFIG_DIRECTORY2)
        print_server_info(nginx_data2)
        save_nginx_data_to_db(nginx_data2)
