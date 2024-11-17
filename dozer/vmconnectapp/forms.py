''' forms.py '''
from django import forms
from .models import Vms

class VmForm(forms.ModelForm):
    ''' Форма редактирования кастомного поля cms '''
    class Meta:
        model = Vms
        fields = ['cms']
