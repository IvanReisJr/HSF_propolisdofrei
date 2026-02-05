from django.urls import path
from . import views

urlpatterns = [
    # Units URLs
    path('units/', views.unit_list, name='unit_list'),
    path('units/new/', views.unit_create, name='unit_create'),
    path('units/<uuid:pk>/edit/', views.unit_edit, name='unit_edit'),
    path('units/<uuid:pk>/inativar/', views.inativar_unidade, name='inativar_unidade'),
]
