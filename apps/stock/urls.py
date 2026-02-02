from django.urls import path
from . import views

urlpatterns = [
    path('movements/', views.movement_list, name='movement_list'),
    path('movements/new/', views.movement_create, name='movement_create'),
    path('api/stock-level/', views.get_stock_level, name='get_stock_level'),
]
