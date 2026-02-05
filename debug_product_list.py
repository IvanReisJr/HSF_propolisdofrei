
import os
import django
from django.conf import settings
from django.test import RequestFactory
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.products.views import product_list
from apps.categories.models import Category

def test_product_list_context():
    print("--- Verificando Product List Context ---")
    
    User = get_user_model()
    user = User.objects.first()
    
    factory = RequestFactory()
    
    # CASE 1: Default Request (should imply status='active')
    request = factory.get('/products/')
    request.user = user
    
    try:
        response = product_list(request)
        if response.status_code == 200:
            # Inspection of local variables in the frame is hard, 
            # but we can try to inspect the response context if it was a TemplateResponse (render returns HttpResponse but often carries context in testing)
            # Actually standard 'render' returns HttpResponse which renders immediately.
            # We will rely on content check or mocking render if needed, but let's check content for category names first.
            
            content = response.content.decode('utf-8')
            
            # Check if categories are passed
            print("Verificando se categorias aparecem no HTML (Dropdown)...")
            cats = Category.objects.all()[:3]
            if not cats:
                 print("⚠ Sem categorias no banco para testar.")
            
            found_count = 0
            for cat in cats:
                if cat.name in content:
                    found_count += 1
            
            if found_count > 0:
                print(f"✔ Categorias encontradas no HTML: {found_count}/{len(cats)}")
            else:
                print("✘ Nenhuma categoria encontrada no HTML da lista!")

            # Check for filter inputs
            if 'name="q"' in content:
                 print("✔ Input de busca encontrado.")
            if 'name="category"' in content:
                 print("✔ Select de categoria encontrado.")
            if 'name="status"' in content:
                 print("✔ Select de status encontrado.")

        else:
            print(f"✘ View retornou status {response.status_code}")

    except Exception as e:
        print(f"✘ Erro ao executar view: {e}")

if __name__ == "__main__":
    test_product_list_context()
