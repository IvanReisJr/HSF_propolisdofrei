import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.products.views import product_list, product_create, packaging_list, packaging_create

User = get_user_model()

print("=" * 60)
print("🔍 TESTE FINAL: TODAS AS VIEWS DE PRODUTOS E EMBALAGENS")
print("=" * 60)

user = User.objects.filter(is_superuser=True).first()
if not user:
    print("❌ Nenhum superusuário encontrado!")
    exit(1)

print(f"✅ Usuário de teste: {user.email}\n")

factory = RequestFactory()

tests = [
    (product_list, "/products/", "Lista de Produtos"),
    (product_create, "/products/new/", "Criar Produto"),
    (packaging_list, "/packagings/", "Lista de Embalagens"),
    (packaging_create, "/packagings/new/", "Criar Embalagem"),
]

print("📋 TESTANDO TODAS AS VIEWS:")
print("-" * 60)

results = []
for view_func, url, name in tests:
    try:
        request = factory.get(url)
        request.user = user
        response = view_func(request)
        
        if response.status_code == 200:
            status = "✅ OK"
            results.append(True)
        else:
            status = f"❌ ERRO {response.status_code}"
            results.append(False)
        print(f"{name:30} {status}")
    except Exception as e:
        print(f"{name:30} ❌ EXCEPTION: {str(e)[:50]}")
        results.append(False)

print("\n" + "=" * 60)
print("📊 RESUMO FINAL:")
print("=" * 60)
ok_count = sum(results)
print(f"✅ Funcionando: {ok_count}/{len(tests)}")
print(f"❌ Com erro: {len(tests) - ok_count}/{len(tests)}")

if ok_count == len(tests):
    print("\n🎉 PERFEITO! TODAS AS VIEWS ESTÃO FUNCIONANDO!")
    print("\n✅ URLs Disponíveis:")
    print("   - /products/ (Lista)")
    print("   - /products/new/ (Criar)")
    print("   - /packagings/ (Lista)")
    print("   - /packagings/new/ (Criar)")
else:
    print("\n⚠️ Algumas views ainda apresentam problemas.")
print("=" * 60)
