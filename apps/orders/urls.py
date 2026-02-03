from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('new/', views.order_create, name='order_create'),
    path('<uuid:pk>/', views.order_detail, name='order_detail'),
    path('<uuid:pk>/confirm/', views.order_confirm, name='order_confirm'),
    path('<uuid:pk>/cancel/', views.order_cancel, name='order_cancel'),
    path('<uuid:pk>/delete/', views.order_delete, name='order_delete'),
]
