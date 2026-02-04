
import os
import django
from django.conf import settings
from django.test import RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.template import engines

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.products.views import product_create

def test_product_create_view():
    print("--- Verificando View de Criação de Produto ---")
    
    # DEBUG: Check template content seen by Django
    try:
        engine = engines['django']
        template = engine.get_template('products/product_form.html')
        print(f"✔ Template Encontrado: {template.origin.name}")
        
        # Read the file from the origin path to see what Django sees
        with open(str(template.origin.name), 'r', encoding='utf-8') as f:
            content = f.read()
            print("--- Conteúdo do Template (Primeiras linhas com 'category_id') ---")
            for line in content.splitlines():
                if 'category_id' in line:
                    print(f"File Line: {line.strip()}")
            print("-------------------------------------------------------------")
            
    except Exception as e:
        print(f"✘ Erro ao carregar template diretamente: {e}")

    # 1. Check URL Resolution
    try:
        url = reverse('product_create')
        print(f"✔ URL 'product_create' resolve para: {url}")
    except Exception as e:
        print(f"✘ Erro ao resolver URL 'product_create': {e}")
        return

    # 2. Check View Response (GET)
    User = get_user_model()
    user = User.objects.first()
    if not user:
        print("⚠ Nenhum usuário encontrado. Criando user mock.")
        user = User(username='test_user', email='test@example.com')
        user.is_superuser = True
        user.save()
        
    print(f"Usando usuário: {user}")

    factory = RequestFactory()
    request = factory.get(url)
    request.user = user
    
    # Message middleware mock
    from django.contrib.messages.storage.fallback import FallbackStorage
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    try:
        response = product_create(request)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✔ View retornou 200 OK.")
        else:
            print(f"✘ Status inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"✘ Exceção ao executar a view: {e}")
    
if __name__ == "__main__":
    test_product_create_view()
