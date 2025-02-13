''' Domans app urls.py '''
from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import index, NginxDomainViewSet, nginx_data

router = SimpleRouter()
router.register(r'nginx_domains', NginxDomainViewSet, basename='nginx_domains')

urlpatterns = [
    path('', index, name='index'),
    path('nginx_data/', nginx_data, name='nginx_data'),  # API без пагинации
]

urlpatterns += router.urls
