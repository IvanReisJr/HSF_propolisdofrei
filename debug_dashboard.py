
import os
import django
from django.conf import settings
from django.test import RequestFactory
from django.template import engines
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from config.views import dashboard

def test_dashboard_view():
    print("--- Verificando Dashboard View ---")
    
    # 1. Check template file content for literal curly braces
    try:
        engine = engines['django']
        template = engine.get_template('dashboard.html')
        print(f"✔ Template Encontrado: {template.origin.name}")
    except Exception as e:
        print(f"✘ Erro ao carregar template: {e}")
        return

    # 2. Render View
    User = get_user_model()
    # Create or get a user with a distributor mock? 
    # For now just a basic superuser to trigger the 'if superuser' path
    user = User.objects.first()
    if not user:
        user = User(username='test_admin', email='test@admin.com')
        user.is_superuser = True
        user.save()
        
    print(f"Usando usuário: {user}")

    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    
    try:
        response = dashboard(request)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            print("✔ View retornou 200 OK.")
            
            # Check if the tags were rendered or appear literally
            if '{{ user.distributor' in content:
                print("✘ ERRO: Tag {{ user.distributor... }} encontrada literalmente no output!")
            else:
                print("✔ Tag {{ user.distributor... }} processada corretamente.")
                
            if '{{ stats.pending_orders' in content:
                 print("✘ ERRO: Tag {{ stats.pending_orders... }} encontrada literalmente no output!")
            else:
                 print("✔ Tag {{ stats.pending_orders... }} processada corretamente.")
            
            # Print a snippet of the relevant section
            if 'Gestão ativa da unidade' in content:
                start = content.find('Gestão ativa da unidade')
                end = content.find('pendentes hoje', start) + 20
                print(f"Snippet renderizado: ...{content[start:end]}...")
                
        else:
            print(f"✘ Status inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"✘ Exceção ao executar a view: {e}")
    
if __name__ == "__main__":
    test_dashboard_view()
