from django.urls import path
from .views import *


urlpatterns = [
    # path('', views.index),
    path('', IndexVms.as_view()),
    path('vmtools/', ViewVMtolls.as_view()),
    path('bados/', ViewBadOS.as_view()),
]