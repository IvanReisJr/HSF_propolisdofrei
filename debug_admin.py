
import sys
import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib import admin
from django.urls import reverse, NoReverseMatch

def check_admin_registry():
    print("--- Verificando Registro do Admin ---")
    
    # Check if Product is registered
    from apps.products.models import Product
    
    if Product in admin.site._registry:
        model_admin = admin.site._registry[Product]
        print(f"Modelo Produto está registrado com: {model_admin}")
        print(f"Classe: {model_admin.__class__.__name__}")
        print(f"Module: {model_admin.__class__.__module__}")
        
        # Check permissions methods
        print(f"has_add_permission: {model_admin.has_add_permission}")
        print(f"get_model_perms: {model_admin.get_model_perms}")
        
        # Check URL
        info = Product._meta.app_label, Product._meta.model_name
        url_name = f'admin:{info[0]}_{info[1]}_add'
        try:
            url = reverse(url_name)
            print(f"URL de adição resolvida: {url} (Nome: {url_name})")
        except NoReverseMatch:
            print(f"NÃO FOI POSSÍVEL resolver a URL: {url_name}")
            
    else:
        print("Modelo Produto NÃO está registrado no admin.site padrão.")
        
    print("\n--- Todos os Modelos Registrados ---")
    for model, model_admin in admin.site._registry.items():
        print(f"{model._meta.label} -> {model_admin.__class__.__name__}")

if __name__ == "__main__":
    check_admin_registry()
