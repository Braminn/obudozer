from django.urls import path
from .views import *
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
]