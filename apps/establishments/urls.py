from django.urls import path
from . import views

urlpatterns = [
    path('', views.establishment_list, name='establishment_list'),
    path('new/', views.establishment_create, name='establishment_create'),
    path('<uuid:pk>/edit/', views.establishment_edit, name='establishment_edit'),
]
