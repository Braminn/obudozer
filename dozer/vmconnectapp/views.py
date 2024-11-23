''' views.py '''

import logging
from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, View
from django.http import HttpResponse

from pyVim.connect import Disconnect
from pyVmomi import vim

from .vconnect import vcenter_connect, dbupdate, update_custom_field

from .models import Vms, Oss
from .forms import VmForm


logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)


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
                field_name="CMS",
                field_value=vm_instance.cms,
            )

            if not success:
                return HttpResponse("Ошибка при обновлении кастомного поля", status=500)

            # # Подключаемся к vCenter и обновляем кастомное поле
            # logger.info('Подключаемся к vCenter...')
            # si = vcenter_connect()
            # custom_field_manager = si.content.customFieldsManager

            # # Используем CreateContainerView для поиска ВМ по имени
            # vms_view = si.content.viewManager.CreateContainerView(si.content.rootFolder, [vim.VirtualMachine], True)
            # vm_from_vc = None
            # for vm_object in vms_view.view:
            #     if vm_object.name == vm_instance.name:  # Поиск по имени
            #         vm_from_vc = vm_object
            #         break

            # logger.debug('vm - %s', vm_from_vc.name)
            # if vm_from_vc:
            #     field_key = None
            #     field_name = "CMS"  # Укажите ваше имя кастомного поля
            #     for field in custom_field_manager.field:
            #         if field.name == field_name:
            #             field_key = field.key
            #             break

            #     if field_key:
            #         try:
            #             custom_field_manager.SetField(entity=vm_from_vc, key=field_key, value=vm_instance.cms)
            #             logger.info("Успешно обновлено кастомное поле: %s", vm_instance.cms)
            #         except vim.fault.NoPermission as e:
            #             logger.error("NoPermission error: %s", e.privilegeId)
            #         except vim.fault.InvalidArgument as e:
            #             logger.error("InvalidArgument error: %s", e.msg)
            #         except vim.fault.InvalidType as e:
            #             logger.error("InvalidType error: %s", e)
            #         except ImportError as e:
            #             logger.error("An unexpected error occurred: %s", str(e))

            # Disconnect(si)

            if request.headers.get('HX-Request'):  # Если запрос через HTMX
                html = f'<td id="custom-field-{vm_instance.id}">{vm_instance.cms}</td>'
                return HttpResponse(html)

        return render(request, 'vmconnectapp/partials/edit_custom_field_form.html', {'form': form, 'vm': vm_instance})


def dbupdte_func(request):
    ''' Кнопка обновления БД '''
    dbupdate()
    return HttpResponse("""<html><script>window.location.replace('/');</script></html>""")
