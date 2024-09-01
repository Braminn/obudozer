from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.views.generic import ListView
from .models import Vms

from django.conf import settings
from pyVim.connect import SmartConnect

from pyVmomi import vim


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

    si = connect()
    content = si.RetrieveContent()
    container = content.rootFolder
    view_type = [vim.VirtualMachine]
    recursive = True
    container_view = content.viewManager.CreateContainerView(
            container, view_type, recursive)
    children = container_view.view

    # Очищаем БД перед обновлением
    Vms.objects.all().delete()

    # Основной цикл заполения БД
    for child in children:
        
        osInfo = {}
        vmtoolsdesc = None
        vmtoolsver = None

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

        x = Vms(name = child.summary.config.name, 
                powerState = child.summary.runtime.powerState,
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
        return Vms.objects.filter(powerState='poweredOn').exclude(name__contains='vCLS')


class IndexVmsPoweredOff(ListView):
    pass


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vmsCount'] = Vms.objects.all().count()
        return context

    def get_queryset(self):
        return Vms.objects.filter(powerState='poweredOn', distroVersion=None).exclude(name__contains='vCLS')
    

# def index(request):

#     if request.POST.get('getData'):
#         dbupdate()

#     # Вывод содержимого
#     vms = Vms.objects.all()
#     vmsCount = Vms.objects.all().count()

#     context = {
#         'vms': vms,
#         'vmsCount': vmsCount
#     }

#     return render(request, 'vmconnectapp/index.html', context)

# def vmtools(request):
#     return render(request, 'vmconnectapp/vmtools.html')


