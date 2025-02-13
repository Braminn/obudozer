from rest_framework import serializers
from .models import Vms


class VmsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vms
        fields = ('name', 'resourcePool', 'powerState')
