from django.urls import path
from . import views

urlpatterns = [
    path('', views.distributor_list, name='distributor_list'),
    path('new/', views.distributor_create, name='distributor_create'),
    path('<uuid:pk>/edit/', views.distributor_edit, name='distributor_edit'),
]
