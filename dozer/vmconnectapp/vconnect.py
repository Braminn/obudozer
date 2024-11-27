''' Все операции с подлкючением и работой pyvmomi vCenter '''
import re
import time
import logging
from functools import wraps

from tqdm import tqdm

from django.conf import settings
from django.db import transaction
from django.utils.timezone import now

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from .models import Vms, Oss, SystemInfo

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


def time_of_function(func):
    """
    Декоратор для отображения времени выполнения функции
    """
    @wraps(func)
    def wrapper(*args, **kwargs):  # Добавляем *args и **kwargs
        t1 = time.time()
        result = func(*args, **kwargs)  # Передаем аргументы в оборачиваемую функцию
        t2 = time.time()
        print(f'Время выполнения функции - {t2 - t1} секунд')
        print('')
        return result  # Возвращаем результат функции
    return wrapper


def get_guest_info(vm):
    """
    Извлекает и парсит данные guestInfo.detailed.data для виртуальной машины.
    Возвращает словарь с ключами prettyName, familyName и distroName.
    """
    try:
        # Извлекаем данные по ключу 'guestInfo.detailed.data'
        detailed_data = next(
            (opt.value for opt in vm.config.extraConfig if opt.key == 'guestInfo.detailed.data'),
            None
        )

        # Если данные найдены, парсим их
        if detailed_data:
            parsed_data = dict(re.findall(r"(\w+)='([^']*)'", detailed_data))
            return {
                "prettyName": parsed_data.get('prettyName'),
                "familyName": parsed_data.get('familyName'),
                "distroName": parsed_data.get('distroName'),
                "distroVersion": parsed_data.get('distroVersion'),
                "kernelVersion": parsed_data.get('kernelVersion'),
                "bitness": parsed_data.get('bitness'),
            }
    except AttributeError:
        # Если vm.config.extraConfig или другие атрибуты отсутствуют
        pass

    # Возвращаем None для всех значений, если данных нет
    return {
        "prettyName": None,
        "familyName": None,
        "distroName": None,
        "distroVersion": None,
        "kernelVersion": None,
        "bitness": None,
    }


def get_custom_field(vm, field_name):
    """
    Извлекает значение кастомного поля по имени.
    """
    try:
        # Построим словарь для поиска по имени кастомного поля
        field_map = {field.key: field.name for field in vm.availableField}
        for field in vm.customValue:
            if hasattr(field, 'key') and field.key in field_map:
                if field_map[field.key] == field_name:
                    return field.value
    except AttributeError:
        return None  # Если customValue или availableField отсутствуют
    return None  # Если поле не найдено


def get_resource_pool_path(resource_pool):
    """
    Построение полного пути для Resource Pool.
    """
    try:
        path = []
        current = resource_pool
        while current:
            path.insert(0, current.name)
            current = current.parent if isinstance(current, vim.ResourcePool) else None
        return '/'.join(path)
    except AttributeError:
        return None  # Если структура Resource Pool нарушена


@time_of_function
def fetch_vcenter_data():
    """
    Основная функция для получения данных из vCenter и сохранения в базу данных.
    """
    print('Начинаем получение данных из vCenter...')
    si = vcenter_connect()
    content = si.RetrieveContent()
    obj_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine,  vim.ResourcePool], True)

    vms = {}
    resource_pools = {}
    total_vms = len(obj_view.view)
    print(f"Всего объектов для обработки: {total_vms}")

    for vm in tqdm(obj_view.view, desc="Обработка объектов", unit="OBJ"):
        if isinstance(vm, vim.VirtualMachine):
            guest_details = get_guest_info(vm) # Вызываем функцию парсинга guestInfo.detailed.data
            resource_pool_path = (get_resource_pool_path(vm.resourcePool) if vm.resourcePool else None) # Вызываем функцию преобразования полного пути ресурсного пула
            vms[vm.name] = {
                "powerState": vm.runtime.powerState if vm.runtime else None,
                "resourcePool": resource_pool_path,
                "ipAdress": vm.guest.ipAddress if vm.guest and vm.guest.ipAddress else None,
                "toolsStatus": vm.guest.toolsStatus if vm.guest and vm.guest.toolsStatus else None,
                "vmtoolsdescription": next((opt.value for opt in getattr(vm.config, 'extraConfig', []) if getattr(opt, 'key', None) == 'guestinfo.vmtools.description'), None),
                "vmtoolsversionNumber": next((opt.value for opt in getattr(vm.config, 'extraConfig', []) if getattr(opt, 'key', None) == 'guestinfo.vmtools.versionNumber'), None),
                "prettyName": guest_details["prettyName"],
                "familyName": guest_details["familyName"],
                "distroName": guest_details["distroName"],
                "distroVersion": guest_details["distroVersion"],
                "kernelVersion": guest_details["kernelVersion"],
                "bitness": guest_details["bitness"],
                "cms": get_custom_field(vm, "cms"),
            }
        elif isinstance(vm, vim.ResourcePool):
            resource_pools[vm.name] = {
                "parent": vm.parent.name if vm.parent else None,
            }

    # print("Vms:")
    # for vm_name, vm_data in vms.items():
    #     print(f"{vm_name}: {vm_data}")
    #     print(" ")

    obj_view.Destroy()
    Disconnect(si)
    print('Получение данных ид vCenter завершено.')

    return vms


@time_of_function
def save_vms_to_db(vms):
    """
    Очищает таблицу Vms и сохраняет объект vms в базу данных.
    """
    print('Начинаем сохранение данных в бд...')
    try:
        with transaction.atomic():
            # Удаляем все существующие записи
            Vms.objects.all().delete()
            print("Все записи удалены из таблицы Vms.")

            # Сохраняем новые данные
            for vm_name, vm_data in vms.items():
                Vms.objects.create(
                    name=vm_name,
                    powerState=vm_data.get("powerState"),
                    resourcePool=vm_data.get("resourcePool"),
                    ipAdress=vm_data.get("ipAdress"),
                    toolsStatus=vm_data.get("toolsStatus"),
                    vmtoolsdescription=vm_data.get("vmtoolsdescription"),
                    vmtoolsversionNumber=vm_data.get("vmtoolsversionNumber"),
                    prettyName=vm_data.get("prettyName"),
                    familyName=vm_data.get("familyName"),
                    distroName=vm_data.get("distroName"),
                    distroVersion=vm_data.get("distroVersion"),
                    kernelVersion=vm_data.get("kernelVersion"),
                    bitness=vm_data.get("bitness"),
                    cms=vm_data.get("cms"),
                )
        print("Данные успешно сохранены в базу данных.")
    except ImportError as e:
        print(f"Ошибка при сохранении данных: {e}")


@time_of_function
def sync_pretty_names_with_db(vms):
    """
    Сравнивает значение prettyName в объекте vms с моделью Oss.
    Если встречается новое значение, оно добавляется в модель Oss.
    """
    print('Начинаем поиск новых ОС...')
    # Получаем все существующие prettyName из модели Oss
    existing_pretty_names = set(Oss.objects.values_list('prettyName', flat=True))

    # Собираем все unique prettyName из объекта vms
    new_pretty_names = {
        vm_data.get('prettyName')
        for vm_data in vms.values()
        if vm_data.get('prettyName')  # Учитываем только не None значения
    }

    # Находим новые prettyName, которых еще нет в модели Oss
    unique_pretty_names = new_pretty_names - existing_pretty_names

    # Добавляем новые записи в модель Oss
    new_oss_entries = [Oss(prettyName=name) for name in unique_pretty_names]
    Oss.objects.bulk_create(new_oss_entries)
    print(f"Добавлено новых записей: {len(new_oss_entries)}")


def last_db_update_time():
    """
    Обновляет запись с датой и временем последнего обновления базы данных.
    """
    SystemInfo.objects.update_or_create(
        name="last_update_time",
        defaults={"value": now().isoformat()}  # Сохраняем дату и время в формате ISO
    )


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
