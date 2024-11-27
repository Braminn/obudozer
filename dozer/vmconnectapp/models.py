''' models.py '''
import os
import re
import logging
from django.db import models


class Vms(models.Model):
    ''' Модель, в кторую мы полудачем данные о все ВМ '''
    name = models.CharField(max_length=150)
    resourcePool = models.CharField(max_length=150, null=True)
    powerState = models.CharField(max_length=150, null=True)
    ipAdress = models.CharField(max_length=150, null=True)
    toolsStatus = models.CharField(max_length=150, null=True)
    vmtoolsdescription = models.CharField(max_length=150, null=True)
    vmtoolsversionNumber = models.IntegerField(null=True)
    prettyName = models.CharField(max_length=150, null=True)
    familyName = models.CharField(max_length=150, null=True)
    distroName = models.CharField(max_length=150, null=True)
    distroVersion = models.CharField(max_length=150, null=True)
    kernelVersion = models.CharField(max_length=150, null=True)
    bitness = models.CharField(max_length=150, null=True)
    cms = models.CharField(max_length=150, null=True)
    owner = models.CharField(max_length=150, null=True)

    def __str__(self):
        return str(self.name)


class Oss(models.Model):
    ''' Модель, в которую мы получаем все ОС '''
    prettyName = models.CharField(max_length=150, null=True)
    expirationDate = models.DateField(null=True, blank=True, default=None)

    def __str__(self):
        return str(self.prettyName)

    class Meta:
        ''' Дополнительные имена для админ-панели '''
        verbose_name = 'Операционные системы'
        verbose_name_plural = 'Операционная система'
        ordering = ('prettyName',)


class SystemInfo(models.Model):
    ''' Служебная модель '''
    name = models.CharField(max_length=255, unique=True)
    value = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}: {self.value}"


# Путь к папкам с конфигурациями Nginx
NGINX_SITES_ENABLED = '/home/ladmin/nginx-configurations-obu-main/sites-enabled'
NGINX_SSL = '/home/ladmin/nginx-configurations-obu-main/ssl'

# NGINX_SITES_ENABLED = '/home/stegancevva@ADMLR.LOC/py/nginx-configurations-obu-main/sites-enabled/'
# NGINX_SSL = '/home/stegancevva@ADMLR.LOC/py/nginx-configurations-obu-main/ssl'

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Регулярное выражение для поиска доменных имен
DOMAIN_REGEX = re.compile(r'\s*server_name\s+([a-zA-Z0-9.-]+);')

class Domain(models.Model):
    """
    Модель для хранения доменных имен.
    """
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.name)


def parse_nginx_config():
    """
    Парсит конфигурационные файлы Nginx для извлечения доменных имен.
    """
    domains = set()
    config_dirs = [NGINX_SITES_ENABLED, NGINX_SSL]

    for config_dir in config_dirs:
        if not os.path.isdir(config_dir):
            logging.warning(f"Директория не найдена: {config_dir}")
            continue

        logging.info(f"Читаем файлы из директории: {config_dir}")
        for filename in os.listdir(config_dir):
            file_path = os.path.join(config_dir, filename)
            if not os.path.isfile(file_path):
                logging.warning(f"Пропускаем, так как это не файл: {file_path}")
                continue

            try:
                with open(file_path, 'r') as file:
                    content = file.read()
                    matches = DOMAIN_REGEX.findall(content)

                    if matches:
                        logging.info(f"Найдены домены в файле {filename}: {', '.join(matches)}")
                        domains.update(matches)
                    else:
                        logging.info(f"В файле {filename} доменные имена не найдены")
            except Exception as e:
                logging.error(f"Ошибка при чтении файла {file_path}: {e}")

    logging.info(f"Обнаружено всего доменов: {len(domains)}")
    return domains


def save_domains_to_db():
    """
    Сохраняет найденные доменные имена в базу данных.
    """
    domains = parse_nginx_config()

    if not domains:
        logging.warning("Нет доменов для сохранения в базу данных")
        return

    for domain in domains:
        try:
            obj, created = Domain.objects.get_or_create(name=domain)
            if created:
                logging.info(f"Добавлен новый домен: {domain}")
            else:
                logging.info(f"Домен уже существует: {domain}")
        except Exception as e:
            logging.error(f"Ошибка при сохранении домена {domain}: {e}")
