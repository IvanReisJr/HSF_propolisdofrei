from django.urls import path
from . import views

urlpatterns = [
    path('', views.packaging_list, name='packaging_list'),
    path('new/', views.packaging_create, name='packaging_create'),
    path('<uuid:pk>/edit/', views.packaging_edit, name='packaging_edit'),
    path('<uuid:pk>/inativar/', views.inativar_embalagem, name='inativar_embalagem'),
]
