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
                    NginxConfig.objects.create(
                        domain=domain,
                        listen_ports=config.get("listen", []),
                        ip_addresses=config.get("ip_addresses", [])
                    )

        print('Update')
        CONFIG_DIRECTORY = "/home/stegancevva@admlr.loc/Doc/Python/nginx-configurations-obu/"
        nginx_data = analyze_all_configs(CONFIG_DIRECTORY)
        print_server_info(nginx_data)
        save_nginx_data_to_db(nginx_data)
