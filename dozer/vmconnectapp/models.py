from django.db import models


class Vms(models.Model):
    name = models.CharField(max_length=50)
    powerState = models.CharField(max_length=50, null=True)
    ipAdress = models.CharField(max_length=50, null=True)
    toolsStatus = models.CharField(max_length=50, null=True)
    vmtoolsdescription = models.CharField(max_length=50, null=True)
    vmtoolsversionNumber = models.IntegerField(null=True)
    prettyName = models.CharField(max_length=50, null=True)
    familyName = models.CharField(max_length=50, null=True)
    distroName = models.CharField(max_length=50, null=True)
    distroVersion = models.CharField(max_length=50, null=True)
    kernelVersion = models.CharField(max_length=50, null=True)
    bitness = models.CharField(max_length=50, null=True)

    def __str__(self):
        return self.name
    
