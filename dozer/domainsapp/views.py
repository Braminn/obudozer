''' Domans app view.py '''
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.viewsets import ReadOnlyModelViewSet
from vmconnectapp.models import NginxDomain
from .serializers import NginxDomainSerializer

def index(request):
    """Главная страница с Grid.js"""
    return render(request, 'domainsapp/index.html')

def flatten_list(nested_list):
    """Разворачивает вложенные списки в один уровень"""
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))  # Рекурсивно раскрываем вложенные списки
        else:
            flat_list.append(str(item))  # Приводим к строке
    return flat_list

def nginx_data(request):
    """Группирует конфигурации по домену и возвращает JSON"""
    domains = NginxDomain.objects.all()
    data = []

    for domain in domains:
        configs = domain.configs.all()

        if configs:
            sources = [config.source or "No config" for config in configs]
            waf_status = any(config.waf for config in configs)  # Если у любого конфига WAF True, показываем ✅

            # Разворачиваем вложенные списки IP-адресов и портов
            ip_addresses = flatten_list([config.ip_addresses for config in configs if config.ip_addresses])
            listen_ports = flatten_list([config.listen_ports for config in configs if config.listen_ports])

            data.append({
                "domain_name": domain.domain_name,
                "source": ", ".join(sources),
                "waf": "✅" if waf_status else "",
                "ip_addresses": ", ".join(sorted(set(ip_addresses))) if ip_addresses else "No IPs",
                "listen_ports": ", ".join(sorted(set(listen_ports))) if listen_ports else "No Ports"
            })
        else:
            data.append({
                "domain_name": domain.domain_name,
                "source": "No config",
                "waf": "",
                "ip_addresses": "No IPs",
                "listen_ports": "No Ports"
            })

    return JsonResponse({"data": data})

class NginxDomainViewSet(ReadOnlyModelViewSet):
    """API для списка доменов с конфигурациями"""
    queryset = NginxDomain.objects.all()
    serializer_class = NginxDomainSerializer
