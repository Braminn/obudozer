''' Domans app urls.py '''
from django.urls import path
from .views import NginxDomainConfigListView

urlpatterns = [
    path('', NginxDomainConfigListView.as_view(), name='nginx_domain_config_list'),
]
