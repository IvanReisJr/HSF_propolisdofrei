from django.urls import path
from . import views

urlpatterns = [
    path('logs/', views.audit_list, name='audit_list'),
]
