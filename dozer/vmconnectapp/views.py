''' views.py '''
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, View
from django.utils.timezone import make_aware, localtime
from django.http import HttpResponse
from django.urls import reverse

from .vconnect import fetch_vcenter_data, save_vms_to_db, sync_pretty_names_with_db, update_custom_field, last_db_update_time

from .models import Vms, Oss, SystemInfo, Domain
from .forms import VmForm


logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

executor = ThreadPoolExecutor(max_workers=1)  # Ограничиваем до одного фонового потока

class IndexVms(ListView):
    model = Vms
    template_name = 'vmconnectapp/index.html'
    context_object_name = 'vms'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vmsCount'] = Vms.objects.all().count()
        context['poweredOn'] = Vms.objects.filter(powerState='poweredOn').exclude(name__contains='vCLS').count()
        context['poweredOff'] = Vms.objects.filter(powerState='poweredOff').count()
        context['techVM'] = Vms.objects.filter(name__contains='vCLS').count()
        return context

    def get_queryset(self):
        return Vms.objects.filter(powerState='poweredOn').exclude(name__contains='vCLS').order_by('resourcePool')

    # Отобразить уникальные ОС
    # q = Oss.objects.values('prettyName').distinct()
    # print ('Ответ', q) # See for yourself.

    # if Oss.objects.filter(prettyName = "Ubuntu 22.04.3 LTS").exists():
    #     print("в наборе есть объекты")
    # else:
    #     print("объекты в наборе отсутствуют")


class IndexVmsPoweredOff(ListView):
    model = Vms
    template_name = 'vmconnectapp/vmspoweredoff.html'
    context_object_name = 'vms'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['poweredOff'] = Vms.objects.filter(powerState='poweredOff').count()
        return context

    def get_queryset(self):
        return Vms.objects.filter(powerState='poweredOff')


class IndexVmstechVM(ListView):
    model = Vms
    template_name = 'vmconnectapp/techvm.html'
    context_object_name = 'vms'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['techVM'] = Vms.objects.filter(name__contains='vCLS').count()
        return context

    def get_queryset(self):
        return Vms.objects.filter(name__contains='vCLS')


class IndexVmsAll(ListView):
    model = Vms
    template_name = 'vmconnectapp/vmsall.html'
    context_object_name = 'vms'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vmsCount'] = Vms.objects.all().count()
        return context

    def get_queryset(self):
        return Vms.objects.all()


class ViewVMtolls(ListView):
    model = Vms
    template_name = 'vmconnectapp/vmtools.html'
    context_object_name = 'vms'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['badToolsCount'] = Vms.objects.filter(powerState='poweredOn', distroVersion=None).exclude(name__contains='vCLS').count()
        return context

    def get_queryset(self):
        return Vms.objects.filter(powerState='poweredOn', distroVersion=None).exclude(name__contains='vCLS')


class ViewBadOS(ListView):
    model = Vms
    template_name = 'vmconnectapp/bados.html'
    context_object_name = 'vms'

    # print('OLD-OS')
    expiredOSAfter = Oss.objects.filter(expirationDate__gt = datetime.now(),
                                        expirationDate__lt = datetime.now() + timedelta(days=365))
    expiredOSlistAfteYear = expiredOSAfter.values_list('prettyName', flat=True)
    # print(expiredOSlistAfteYear)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        expiredOS = Oss.objects.filter(expirationDate__lt = datetime.now())
        expiredOSlist = expiredOS.values_list('prettyName', flat=True)

        expiredOSAfter = Oss.objects.filter(expirationDate__gt = datetime.now(),
                                            expirationDate__lt = datetime.now() + timedelta(days=365))
        expiredOSlistAfter = expiredOSAfter.values_list('prettyName', flat=True)

        context['vmsCount'] = Vms.objects.all().count()
        context['poweredOn'] = Vms.objects.filter(powerState='poweredOn').exclude(name__contains='vCLS').count()
        context['poweredOff'] = Vms.objects.filter(powerState='poweredOff').count()
        context['badToolsCount'] = Vms.objects.filter(powerState='poweredOn', distroVersion=None).exclude(name__contains='vCLS').count()

        context['badOSCount'] = Vms.objects.filter(prettyName__in=expiredOSlist, powerState='poweredOn').count()
        context['badOSCountAfter'] = Vms.objects.filter(prettyName__in=expiredOSlistAfter, powerState='poweredOn').count()

        return context


class ViewBadOSExport(ListView):
    model = Vms
    template_name = 'vmconnectapp/badosexport.html'
    context_object_name = 'vms'

    expiredOSAfter = Oss.objects.filter(expirationDate__gt = datetime.now(),
                                        expirationDate__lt = datetime.now() + timedelta(days=365))
    expiredOSlistAfteYear = expiredOSAfter.values_list('prettyName', flat=True)
    # print(expiredOSlistAfteYear)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        logger.info('hello!')
        expiredOS = Oss.objects.filter(expirationDate__lt = datetime.now())
        expiredOSlist = expiredOS.values_list('prettyName', flat=True)

        expiredOSAfter = Oss.objects.filter(expirationDate__gt = datetime.now(),
                                            expirationDate__lt = datetime.now() + timedelta(days=365))
        expiredOSlistAfter = expiredOSAfter.values_list('prettyName', flat=True)

        context['vmsCount'] = Vms.objects.all().count()
        context['poweredOn'] = Vms.objects.filter(powerState='poweredOn').exclude(name__contains='vCLS').count()
        context['poweredOff'] = Vms.objects.filter(powerState='poweredOff').count()
        context['badToolsCount'] = Vms.objects.filter(powerState='poweredOn', distroVersion=None).exclude(name__contains='vCLS').count()

        context['badOSCount'] = Vms.objects.filter(prettyName__in=expiredOSlist, powerState='poweredOn').count()
        context['badOSCountAfter'] = Vms.objects.filter(prettyName__in=expiredOSlistAfter, powerState='poweredOn').count()

        return context

    def get_queryset(self):
        expiredOS = Oss.objects.filter(expirationDate__lt = datetime.now())
        expiredOSlist = expiredOS.values_list('prettyName', flat=True)

        return Vms.objects.filter(prettyName__in=expiredOSlist, powerState='poweredOn').order_by('prettyName').order_by('resourcePool')


#--------------------------------------------------------------------------------------------------------------------------------------------


class VmListView(View):
    ''' Отображение страницы vm_list.html '''
    def get(self, request):
        ''' Получаем все виртуальные машины '''
        vms = Vms.objects.all()
        return render(request, 'vmconnectapp/vm_list.html', {'vms': vms})


class VmEditCancelView(View):
    ''' Отмена редактирования в форме '''
    def get(self, request, vm_id):
        logger.debug('Видим GET кнопки Отмена')
        vm_instance = get_object_or_404(Vms, id=vm_id)
        html = f'<td id="custom-field-{vm_instance.id}">{vm_instance.custom_field}</td>'
        return HttpResponse(html)

class VmEditView(View):
    def get(self, request, vm_id):
        logger.debug('Видим GET')
        vm_instance = get_object_or_404(Vms, id=vm_id)
        form = VmForm(instance=vm_instance)
        if request.headers.get('HX-Request'):  # Если запрос через HTMX
            logger.debug('Видим HX-Request')
            return render(request, 'vmconnectapp/partials/edit_custom_field_form.html', {'form': form, 'vm': vm_instance})
        return render(request, 'vmconnectapp/partials/edit_custom_field_form.html', {'form': form, 'vm': vm_instance})

    def post(self, request, vm_id):
        logger.debug('Видим POST')
        vm_instance = get_object_or_404(Vms, id=vm_id)
        form = VmForm(request.POST, instance=vm_instance)

        if form.is_valid():
            # Сохраняем значение кастомного поля в базе данных
            vm_instance = form.save()
            logger.debug('form.save - %s', vm_instance)

            # Вызываем функцию для обновления кастомного поля
            success = update_custom_field(
                vm_name=vm_instance.name,
                field_name="cms",
                field_value=vm_instance.cms,
            )

            if not success:
                return HttpResponse("Ошибка при обновлении кастомного поля", status=500)

            if request.headers.get('HX-Request'):  # Если запрос через HTMX
                # Возврат нового HTML с HTMX-атрибутами
                edit_url = reverse('edit_custom_field', args=[vm_instance.id])
                html = f'''
                <div id="custom-field-{vm_instance.id}" 
                    hx-get="{edit_url}" 
                    hx-target="this" 
                    hx-swap="outerHTML" 
                    hx-trigger="click">
                    {vm_instance.cms}
                </div>
                '''
                return HttpResponse(html)

        return render(request, 'vmconnectapp/partials/edit_custom_field_form.html', {'form': form, 'vm': vm_instance})


def dbupdate_task():
    """
    Задача для обновления базы данных.
    """
    vms = fetch_vcenter_data()
    save_vms_to_db(vms)
    sync_pretty_names_with_db(vms)
    last_db_update_time()
    return "Обновлено!"  # Вернуть сообщение о завершении работы


def dbupdte_func(request):
    """
    Кнопка обновления БД.
    """
    # Запускаем задачу в отдельном потоке и ждем завершения
    future = executor.submit(dbupdate_task)
    result = future.result()  # Дождемся завершения задачи и получим результат
    logger.info('Результат ассинхронной функции - %s', result)

    last_update = SystemInfo.objects.filter(name="last_update_time").first()
    if last_update and last_update.value:
        # Преобразуем строку в объект datetime
        update_time = datetime.fromisoformat(last_update.value)
        # Делаем время "осведомленным" о часовом поясе
        aware_time = make_aware(update_time) if update_time.tzinfo is None else update_time
        # Приводим к локальному часовому поясу
        local_time = localtime(aware_time)
        # Форматируем дату
        readable_time = local_time.strftime("%d.%m.%Y, %H:%M")
        return HttpResponse(f'<div id="update-status">{readable_time}</div>')
    else:
        return HttpResponse('<div id="update-status">Время обновления отсутствует</div>')


class DomainListView(ListView):
    model = Domain
    template_name = 'domains/domain_list.html'  # Путь к вашему шаблону
    context_object_name = 'domains'  # Контекст, который будет доступен в шаблоне
