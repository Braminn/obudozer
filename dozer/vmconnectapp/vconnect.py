''' Все операции с подлкючением и работой pyvmomi vCenter '''
import logging

from django.conf import settings

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from .models import Vms, Oss

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
    
    # ---------------------

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


def update_custom_field(vm_name, field_name, field_value):
    """
    Обновляет значение кастомного поля в vCenter для виртуальной машины.

    :param vm_name: Имя виртуальной машины
    :param field_name: Имя кастомного поля
    :param field_value: Новое значение для кастомного поля
    :return: True, если обновление прошло успешно, иначе False
    """
    try:
        # Подключаемся к vCenter
        logger.info('Подключаемся к vCenter...')
        si = vcenter_connect()
        content = si.RetrieveContent()

        # Создаём контейнер для поиска виртуальных машин
        vms_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
        vm = None
        for vm_object in vms_view.view:
            if vm_object.name == vm_name:
                vm = vm_object
                break
        vms_view.Destroy()

        if not vm:
            logger.error("Виртуальная машина '%s' не найдена в vCenter", vm_name)
            return False

        # Поиск ключа кастомного поля
        logger.debug('vm - %s', vm.name)
        custom_field_manager = content.customFieldsManager
        field_key = None
        for field in custom_field_manager.field:
            if field.name == field_name:
                field_key = field.key
                break

        if not field_key:
            logger.error("Кастомное поле '%s' не найдено", field_name)
            return False

        # Устанавливаем значение кастомного поля
        custom_field_manager.SetField(entity=vm, key=field_key, value=field_value)
        logger.info("Успешно обновлено кастомное поле '%s' для ВМ '%s'", field_name, vm_name)

        return True

    except ImportError as e:
        logger.error("Ошибка при обновлении кастомного поля: %s", e)
        return False

    finally:
        Disconnect(si)
