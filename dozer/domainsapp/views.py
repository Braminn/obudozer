''' Domans app view.py '''
from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
from vmconnectapp.models import NginxDomain
from .serializers import NginxDomainSerializer

def index(request):
    """Главная страница с Grid.js"""
    return render(request, 'domainsapp/index.html')

class NginxDomainViewSet(ReadOnlyModelViewSet):
    """API для списка доменов с конфигурациями"""
    queryset = NginxDomain.objects.all()
    serializer_class = NginxDomainSerializer
