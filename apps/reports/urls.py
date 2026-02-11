from django.urls import path
from . import views

urlpatterns = [
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('inventory/pdf/', views.inventory_pdf, name='inventory_pdf'),
]
