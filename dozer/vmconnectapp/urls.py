''' forms.py '''
from django.urls import path
from .views import (
    index,
    VmsAPIView,
    vms_data,
    vms_update,

    IndexVmsPoweredOff,
    IndexVmstechVM,
    IndexVmsAll,
    ViewVMtolls,
    ViewBadOS,
    ViewBadOSExport,
    VmListView,
    VmEditView,
    VmEditCancelView,
    )
from . import views


urlpatterns = [
    path('', index),
    path('api/v1/vmslist', VmsAPIView.as_view()),
    path('api/v1/data', vms_data, name='vms_data'),
    path('api/v1/data/update/', vms_update, name='vms_update'),

    path('vmspoweredoff/', IndexVmsPoweredOff.as_view()),
    path('techvm/', IndexVmstechVM.as_view()),
    path('vmsall/', IndexVmsAll.as_view()),
    path('dbupdte_func', views.dbupdte_func, name='dbupdte_func'),
    path('vmtools/', ViewVMtolls.as_view()),
    path('bados/', ViewBadOS.as_view()),
    path('badexport/', ViewBadOSExport.as_view()),
    path('vm_list/', VmListView.as_view(), name='vm_list'),
    path('vm/edit/<int:vm_id>/', VmEditView.as_view(), name='edit_custom_field'),
    path('vm/edit/<int:vm_id>/cancel/', VmEditCancelView.as_view(), name='edit_custom_field_cancel'),
]
