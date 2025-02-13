from rest_framework import serializers
from vmconnectapp.models import NginxDomain, NginxConfig

class NginxConfigSerializer(serializers.ModelSerializer):
    """Сериализатор для конфигураций Nginx"""

    class Meta:
        model = NginxConfig
        fields = ['source', 'waf', 'ip_addresses', 'listen_ports']

class NginxDomainSerializer(serializers.ModelSerializer):
    """Сериализатор для доменов с вложенными конфигурациями"""
    configs = NginxConfigSerializer(many=True, read_only=True)

    class Meta:
        model = NginxDomain
        fields = ['domain_name', 'configs']
