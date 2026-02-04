import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from apps.products.views import product_list, product_create, product_edit, packaging_list, packaging_create, packaging_edit

User = get_user_model()

print("=" * 60)
print("🔍 DIAGNÓSTICO DE VIEWS - PRODUTOS E EMBALAGENS")
print("=" * 60)

# Get or create test user
user = User.objects.filter(is_superuser=True).first()
if not user:
    print("❌ Nenhum superusuário encontrado!")
    exit(1)

print(f"✅ Usuário de teste: {user.email}")

# Test with Client (simulates real browser requests)
client = Client()
client.force_login(user)

print("\n📋 TESTANDO VIEWS DE PRODUTOS:")
print("-" * 60)

tests = [
    ("/products/", "Lista de Produtos"),
    ("/products/new/", "Criar Produto"),
    ("/products/packagings/", "Lista de Embalagens"),
    ("/products/packagings/new/", "Criar Embalagem"),
]

results = []
for url, name in tests:
    try:
        response = client.get(url)
        status = "✅ OK" if response.status_code == 200 else f"❌ ERRO {response.status_code}"
        results.append((name, status, response.status_code))
        print(f"{name:30} {status}")
        
        if response.status_code != 200:
            # Try to get error details
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8')
                if 'TemplateSyntaxError' in content:
                    print(f"  └─ Template Syntax Error detectado!")
                elif 'DoesNotExist' in content:
                    print(f"  └─ Objeto não encontrado no banco!")
                elif '500' in str(response.status_code):
                    print(f"  └─ Erro interno do servidor!")
    except Exception as e:
        results.append((name, f"❌ EXCEPTION", 0))
        print(f"{name:30} ❌ EXCEPTION: {str(e)[:50]}")

print("\n" + "=" * 60)
print("📊 RESUMO:")
print("=" * 60)
ok_count = sum(1 for _, status, _ in results if "OK" in status)
print(f"✅ Funcionando: {ok_count}/{len(tests)}")
print(f"❌ Com erro: {len(tests) - ok_count}/{len(tests)}")

if ok_count == len(tests):
    print("\n🎉 TODAS AS VIEWS ESTÃO FUNCIONANDO!")
else:
    print("\n⚠️ ALGUMAS VIEWS APRESENTAM PROBLEMAS")
    print("Verifique os detalhes acima para identificar o erro.")
