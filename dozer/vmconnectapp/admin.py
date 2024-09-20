from django.contrib import admin
from vmconnectapp.models import Vms, Oss


class OssAdmin(admin.ModelAdmin):
    list_display = ("prettyName", "expirationDate")

admin.site.register(Vms)
admin.site.register(Oss, OssAdmin)

