from django.urls import path
from . import views

urlpatterns = [
    path('movements/', views.movement_list, name='movement_list'),
    path('movements/new/', views.movement_create, name='movement_create'),
    path('api/stock-level/', views.get_stock_level, name='get_stock_level'),
    path('entrada/', views.registrar_entrada, name='registrar_entrada'),
    path('saida/', views.registrar_saida, name='registrar_saida'),
    path('dashboard-matriz/', views.dashboard_matriz_consolidado, name='dashboard_matriz_consolidado'),
]
