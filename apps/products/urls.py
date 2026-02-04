from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('new/', views.product_create, name='product_create'),
    
    
    # Product detail/edit - parameterized paths LAST
    path('<uuid:pk>/', views.product_detail, name='product_detail'),
    path('<uuid:pk>/edit/', views.product_edit, name='product_edit'),
]
