''' Domans app urls.py '''
from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import index, NginxDomainViewSet

router = SimpleRouter()
router.register(r'nginx_domains', NginxDomainViewSet, basename='nginx_domains')

urlpatterns = [
    path('', index, name='index'),  # Главная страница
]

urlpatterns += router.urls  # Автоматически добавляем API маршруты
