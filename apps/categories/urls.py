from django.urls import path
from . import views

urlpatterns = [
    path('', views.category_list, name='category_list'),
    path('new/', views.category_create, name='category_create'),
    path('<uuid:pk>/edit/', views.category_edit, name='category_edit'),
]
