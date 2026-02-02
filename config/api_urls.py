from django.urls import path, include
from rest_framework.routers import DefaultRouter

# API desativada temporariamente durante a migração para o Monolito
# Se necessário, recriar ViewSets específicos

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
]
