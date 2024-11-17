''' forms.py '''
from django.urls import path
from .views import (
    IndexVms,
    IndexVmsPoweredOff,
    IndexVmstechVM,
    IndexVmsAll,
    ViewVMtolls,
    ViewBadOS,
    ViewBadOSExport,
    VmListView,
    VmEditView,
    VmEditCancelView
    )
from . import views


urlpatterns = [
    # path('', views.index),
    path('', IndexVms.as_view()),
    path('vmspoweredoff/', IndexVmsPoweredOff.as_view()),
    path('techvm/', IndexVmstechVM.as_view()),
    path('vmsall/', IndexVmsAll.as_view()),
    path('dbupdte_func', views.dbupdte_func),
    path('vmtools/', ViewVMtolls.as_view()),
    path('bados/', ViewBadOS.as_view()),
    path('badexport/', ViewBadOSExport.as_view()),
    
    path('vm_list/', VmListView.as_view(), name='vm_list'),
    path('vm/edit/<int:vm_id>/', VmEditView.as_view(), name='edit_custom_field'),
    path('vm/edit/<int:vm_id>/cancel/', VmEditCancelView.as_view(), name='edit_custom_field_cancel'),
]
