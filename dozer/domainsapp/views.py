''' Domans app view.py '''
from django.views.generic import ListView
from vmconnectapp.models import NginxDomain, NginxConfig

class NginxDomainConfigListView(ListView):
    model = NginxDomain
    template_name = 'domainsapp/index.html'
    context_object_name = 'domains'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Сортируем домены по имени
        context['domains'] = NginxDomain.objects.all().order_by('domain_name')
        
        # Создаем словарь для отображения конфигураций по каждому домену
        domain_configs = []
        for domain in context['domains']:
            configs = NginxConfig.objects.filter(domain=domain)
            domain_configs.append({
                'domain': domain,
                'configs': configs
            })
        context['domain_configs'] = domain_configs
        return context
