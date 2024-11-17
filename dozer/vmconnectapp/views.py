''' views.py '''

import logging
from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404, render
# from django.template.loader import render_to_string
from django.views.generic import ListView, View
# from django.urls import reverse
from django.http import HttpResponse
from django.conf import settings

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from .models import Vms, Oss
from .forms import VmForm

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

def vcenter_connect():
    ''' vCenter Connect '''
    service_instance = None
    try:
        service_instance = SmartConnect(host = settings.VC_HOST,
                                        user = settings.VC_USER,
                                        pwd = settings.VC_PWD,
                                        disableSslCertValidation = True)
    except IOError as io_error:
        print(io_error)
    if not service_instance:
        raise SystemExit("Unable to connect to host with supplied credentials.")
    return service_instance


def dbupdate():
    ''' Основная функция заполнения данных из vCinter'''

    logger.info('Подключаемся к vCenter...')
    si = vcenter_connect()

    logger.info('Получаем данные из vCenter...')
    content = si.RetrieveContent()
    container = content.rootFolder
    view_type = [vim.VirtualMachine]
    recursive = True
    container_view = content.viewManager.CreateContainerView(
            container, view_type, recursive)
    children = container_view.view

    # Очищаем БД перед обновлением
    logger.info('Очищаем БД Vms')
    Vms.objects.all().delete()
    # logger.info('Очищаем БД Oss')
    # Oss.objects.all().delete()

    # Функция для получения объекта Resource Pool по его имени
    def get_resource_pool_by_name(content, pool_name):
        # Поиск всех датацентров
        for datacenter in content.rootFolder.childEntity:
            # Поиск всех кластеров и хостов в датацентре
            for cluster in datacenter.hostFolder.childEntity:
                if hasattr(cluster, 'resourcePool'):
                    # Если есть Resource Pool, проверим его и его дочерние объекты
                    rp = cluster.resourcePool
                    found_rp = find_pool_recursive(rp, pool_name)
                    if found_rp:
                        return found_rp
        return None


    def find_pool_recursive(pool, pool_name):
        # Рекурсивная функция для поиска Resource Pool по имени
        if pool is not None and hasattr(pool, 'name'):
            if pool.name == pool_name:
                return pool

        if hasattr(pool, 'resourcePool'):
            for child in pool.resourcePool:
                found = find_pool_recursive(child, pool_name)
                if found:
                    return found
        return None

    def get_resource_pool_path(pool):
        # Функция для получения полного пути Resource Pool
        path = pool.name
        parent = pool.parent
        # Проходим по иерархии объектов до корневого (обычно это кластер)
        while hasattr(parent, 'name'):
            path = f"{parent.name}/{path}"
            parent = parent.parent
        return path

    # Основной цикл заполения БД
    logger.info('Загружаем записи: %s', len(children))
    for child in children:
        # Имя обрабатываемой ВМ
        logger.info(child.summary.config.name)

        full_path_form = None
        osInfo = {}
        vmtoolsdesc = None
        vmtoolsver = None
        cms_cf = None
        owner_cf = None

        for block in child.config.extraConfig:
            if block.key == 'guestinfo.vmtools.description':
                vmtoolsdesc = block.value
            # else:
            #     vmtoolsdesc = None

            if block.key == 'guestinfo.vmtools.versionNumber':
                vmtoolsver = block.value
            # else:
            #     vmtoolsver = None

            if block.key == 'guestInfo.detailed.data':
                osInfo = eval("{'" + block.value.replace('=', "':").replace("' ", "', '") + "}")   

        if 'prettyName' not in osInfo:
            osInfo['prettyName'] = None

        if child.resourcePool is not None and hasattr(child.resourcePool, 'name'):
            # print(child.resourcePool.name)
            # Имя ресурсного пула, путь которого нужно получить
            pool_name = child.resourcePool.name
        else:
            pool_name = None

        # Поиск ресурсного пула
        resource_pool = get_resource_pool_by_name(content, pool_name)
        full_path = None

        if resource_pool:
            # Получение полного пути ресурсного пула
            full_path = get_resource_pool_path(resource_pool)
            # print(f"Полный путь ресурсного пула: {full_path}")
            substring = "Datacenters/ADMLR/host/"
            # Находим индекс начала подстроки
            index = full_path.find(substring)
                    # Если подстрока найдена, обрезаем строку
            if index != -1:
                full_path_form = full_path[index + len(substring):]
            else:
                full_path_form = full_path  # Если подстрока не найдена, оставляем строку без изменений
        else:
            logger.warning("Ресурсный пул с именем %s не найден.", pool_name)

        # print(full_path_form)
        # print(child.customValue)
        # print(" ")
        # resource_pool = child.resourcePool
        # if resource_pool:
        #     print(f"Resource Pool для виртуальной машины {osInfo['prettyName']}: {resource_pool.name}")
        #     resource_pool_name = resource_pool.name
        # else:
        #     resource_pool_name = None
        #     #print(f"Виртуальная машина {osInfo['prettyName']} не присоединена к Resource Pool.")

        if 'familyName' not in osInfo:
            osInfo['familyName'] = None
        if 'distroName' not in osInfo:
            osInfo['distroName'] = None
        if 'distroVersion' not in osInfo:
            osInfo['distroVersion'] = None
        if 'kernelVersion' not in osInfo:
            osInfo['kernelVersion'] = None
        if 'bitness' not in osInfo:
            osInfo['bitness'] = None

        # Заполнение модель Oss уникальными ОС
        if not Oss.objects.filter(prettyName = osInfo['prettyName']).exists():
            #print(osInfo['prettyName'], ' добавлена в список уникальных ОС')
            o = Oss(prettyName = osInfo['prettyName'],)
            o.save()
        #else:
            #print(osInfo['prettyName'], ' уже в списке уникальных ОС')

        if child.customValue:
            for custom_field in child.customValue:
                field_key = custom_field.key
                field_value = custom_field.value

                # Получаем название поля по ключу
                custom_fields_manager = content.customFieldsManager
                for field in custom_fields_manager.field:
                    if field.key == field_key and field.name == 'CMS':
                        # print(f"Custom Attribute '{'CMS'}' for VM '{child.name}': {field_value}")
                        cms_cf = field_value
                    if field.key == field_key and field.name == 'Owner':
                        owner_cf = field_value

        x = Vms(name = child.summary.config.name, 
                powerState = child.summary.runtime.powerState,
                resourcePool = full_path_form,
                ipAdress = child.summary.guest.ipAddress,
                toolsStatus = child.summary.guest.toolsStatus,
                vmtoolsdescription = vmtoolsdesc,
                vmtoolsversionNumber = vmtoolsver,
                prettyName = osInfo['prettyName'],
                familyName = osInfo['familyName'],
                distroName = osInfo['distroName'],
                distroVersion = osInfo['distroVersion'],
                kernelVersion = osInfo['kernelVersion'],
                bitness = osInfo['bitness'],
                cms = cms_cf,
                owner = owner_cf,
                )
        x.save()
    Disconnect(si)


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
            # html = render_to_string('vmconnectapp/partials/edit_custom_field_form.html', {'vm': vm_instance, 'form': form}, request=request)
            # logger.debug(html)
            # return HttpResponse(html)
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

            # Подключаемся к vCenter и обновляем кастомное поле
            logger.info('Подключаемся к vCenter...')
            si = vcenter_connect()
            custom_field_manager = si.content.customFieldsManager

            # Используем CreateContainerView для поиска ВМ по имени
            vms_view = si.content.viewManager.CreateContainerView(si.content.rootFolder, [vim.VirtualMachine], True)
            vm_from_vc = None
            # logger.debug('Начинаем for')
            for vm_object in vms_view.view:
                # logger.debug('vm_object - %s', vm_object.name)
                if vm_object.name == vm_instance.name:  # Поиск по имени
                    vm_from_vc = vm_object
                    break

            logger.debug('vm - %s', vm_from_vc.name)
            if vm_from_vc:
                field_key = None
                field_name = "CMS"  # Укажите ваше имя кастомного поля
                for field in custom_field_manager.field:
                    # logger.debug('field - %s', field)
                    if field.name == field_name:
                        # logger.debug('field.key - %s', field.key)
                        field_key = field.key
                        break
                
                # logger.debug('field_key - %s', field_key)
                if field_key:
                    try:
                        custom_field_manager.SetField(entity=vm_from_vc, key=field_key, value=vm_instance.cms)
                        logger.info("Успешно обновлено кастомное поле: %s", vm_instance.cms)
                    except vim.fault.NoPermission as e:
                        logger.error(f"NoPermission error: {e.privilegeId}")
                    except vim.fault.InvalidArgument as e:
                        logger.error(f"InvalidArgument error: {e.msg}")
                    except vim.fault.InvalidType as e:
                        logger.error(f"InvalidType error: {e}")
                    except Exception as e:
                        logger.error(f"An unexpected error occurred: {str(e)}")

            Disconnect(si)

            if request.headers.get('HX-Request'):  # Если запрос через HTMX
                html = f'<td id="custom-field-{vm_instance.id}">{vm_instance.cms}</td>'
                return HttpResponse(html)

        return render(request, 'vmconnectapp/partials/edit_custom_field_form.html', {'form': form, 'vm': vm_instance})


def dbupdte_func(request):
    ''' Кнопка обновления БД '''
    dbupdate()
    return HttpResponse("""<html><script>window.location.replace('/');</script></html>""")
