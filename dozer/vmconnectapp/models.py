''' models.py '''
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


class NginxDomain(models.Model):
    domain_name = models.CharField(max_length=255, unique=True, verbose_name="Domain Name")

    def __str__(self):
        return str(self.domain_name)

class NginxConfig(models.Model):
    domain = models.ForeignKey(NginxDomain, related_name="configs", on_delete=models.CASCADE)
    listen_ports = models.JSONField(default=list, verbose_name="Listen Ports")
    ip_addresses = models.JSONField(default=list, verbose_name="IP Addresses")
    waf = models.BooleanField(default=False, verbose_name="WAF")

    def __str__(self):
        return f"{self.domain.domain_name} Configuration"
