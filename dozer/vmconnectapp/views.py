# from typing import Any
# from django.db.models.query import QuerySet
# from django.shortcuts import render
from django.views.generic import ListView
from django.http import HttpResponse
from django.conf import settings
from datetime import datetime, timedelta

from pyVim.connect import SmartConnect
from pyVmomi import vim
import atexit

from .models import Vms, Oss


def dbupdate():

    def connect():

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

    print('Подключаемся к vCenter...')
    si = connect()

    print('Получаем данные из vCenter...')
    content = si.RetrieveContent()
    container = content.rootFolder
    view_type = [vim.VirtualMachine]
    recursive = True
    container_view = content.viewManager.CreateContainerView(
            container, view_type, recursive)
    children = container_view.view

    # Очищаем БД перед обновлением
    print('Очищаем БД Vms')
    Vms.objects.all().delete()
    # print('Очищаем БД Oss')
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

    # Рекурсивная функция для поиска Resource Pool по имени
    def find_pool_recursive(pool, pool_name):
        # Проверяем, что объект существует и имеет атрибут 'name'
        if pool is not None and hasattr(pool, 'name'):
            if pool.name == pool_name:
                return pool
        
        # Проверяем, есть ли у объекта дочерние resourcePool
        if hasattr(pool, 'resourcePool'):
            for child in pool.resourcePool:
                found = find_pool_recursive(child, pool_name)
                if found:
                    return found
        return None

    # Функция для получения полного пути Resource Pool
    def get_resource_pool_path(pool):
        path = pool.name
        parent = pool.parent
        # Проходим по иерархии объектов до корневого (обычно это кластер)
        while hasattr(parent, 'name'):
            path = f"{parent.name}/{path}"
            parent = parent.parent
        return path

    # Основной цикл заполения БД
    print('Загружаем записи: ')
    print(len(children))
    for child in children:
        # Имя обрабатываемой ВМ
        print(child.summary.config.name)

        full_path_form = None
        osInfo = {}
        vmtoolsdesc = None
        vmtoolsver = None
        cms_cf = None

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
            print(child.resourcePool.name)
            # Имя ресурсного пула, путь которого нужно получить
            pool_name = child.resourcePool.name
        else:
            pool_name = None
        

        # Поиск ресурсного пула
        resource_pool = get_resource_pool_by_name(content, pool_name)

        if resource_pool:
            # Получение полного пути ресурсного пула
            full_path = get_resource_pool_path(resource_pool)
            print(f"Полный путь ресурсного пула: {full_path}")
        else:
            print(f"Ресурсный пул с именем {pool_name} не найден.")        

        substring = "Datacenters/ADMLR/host/"

        # Находим индекс начала подстроки
        index = full_path.find(substring)

        # Если подстрока найдена, обрезаем строку
        if index != -1:
            full_path_form = full_path[index + len(substring):]
        else:
            full_path_form = full_path  # Если подстрока не найдена, оставляем строку без изменений

        print(full_path_form)  
        # print(child.customValue)
        print(" ")     

        # resource_pool = child.resourcePool
        # if resource_pool:
        #     #print(f"Resource Pool для виртуальной машины {osInfo['prettyName']}: {resource_pool.name}")
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
                            print(f"Custom Attribute '{'CMS'}' for VM '{child.name}': {field_value}")
                            cms_cf = field_value

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
                cms = cms_cf
                )
        x.save()


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
    q = Oss.objects.values('prettyName').distinct()
    print ('Ответ', q) # See for yourself.

    if Oss.objects.filter(prettyName = "Ubuntu 22.04.3 LTS").exists():
        print("в наборе есть объекты")
    else:
        print("объекты в наборе отсутствуют")

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

    print('OLD-OS')
    expiredOSAfter = Oss.objects.filter(expirationDate__gt = datetime.now(),
                                        expirationDate__lt = datetime.now() + timedelta(days=365))
    expiredOSlistAfteYear = expiredOSAfter.values_list('prettyName', flat=True)
    print(expiredOSlistAfteYear)


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

    print('OLD-OS')
    expiredOSAfter = Oss.objects.filter(expirationDate__gt = datetime.now(),
                                        expirationDate__lt = datetime.now() + timedelta(days=365))
    expiredOSlistAfteYear = expiredOSAfter.values_list('prettyName', flat=True)
    print(expiredOSlistAfteYear)


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

    def get_queryset(self):
        expiredOS = Oss.objects.filter(expirationDate__lt = datetime.now())
        expiredOSlist = expiredOS.values_list('prettyName', flat=True)

        return Vms.objects.filter(prettyName__in=expiredOSlist, powerState='poweredOn').order_by('prettyName').order_by('resourcePool')
    


def dbupdte_func(request):
    dbupdate()
    return HttpResponse("""<html><script>window.location.replace('/');</script></html>""")



