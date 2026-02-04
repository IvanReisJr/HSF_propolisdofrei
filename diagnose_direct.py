import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.products.views import product_list, product_create, product_edit, packaging_list, packaging_create, packaging_edit

User = get_user_model()

print("=" * 60)
print("🔍 DIAGNÓSTICO DIRETO DE VIEWS (sem middleware)")
print("=" * 60)

# Get test user
user = User.objects.filter(is_superuser=True).first()
if not user:
    print("❌ Nenhum superusuário encontrado!")
    exit(1)

print(f"✅ Usuário de teste: {user.email}\n")

factory = RequestFactory()

tests = [
    (product_list, "/products/", "Lista de Produtos"),
    (product_create, "/products/new/", "Criar Produto"),
    (packaging_list, "/products/packagings/", "Lista de Embalagens"),
    (packaging_create, "/products/packagings/new/", "Criar Embalagem"),
]

print("📋 TESTANDO VIEWS:")
print("-" * 60)

results = []
for view_func, url, name in tests:
    try:
        request = factory.get(url)
        request.user = user
        response = view_func(request)
        
        status = "✅ OK" if response.status_code == 200 else f"❌ ERRO {response.status_code}"
        results.append((name, status, response.status_code))
        print(f"{name:30} {status}")
        
    except Exception as e:
        error_msg = str(e)
        results.append((name, f"❌ EXCEPTION", 0))
        print(f"{name:30} ❌ EXCEPTION")
        print(f"  └─ {error_msg[:100]}")
        
        # Identify error type
        if "TemplateSyntaxError" in error_msg:
            print(f"  └─ 🔴 ERRO DE SINTAXE NO TEMPLATE")
        elif "DoesNotExist" in error_msg:
            print(f"  └─ 🔴 OBJETO NÃO ENCONTRADO NO BANCO")
        elif "Could not parse" in error_msg:
            print(f"  └─ 🔴 ERRO DE PARSING NO TEMPLATE")

print("\n" + "=" * 60)
print("📊 RESUMO:")
print("=" * 60)
ok_count = sum(1 for _, status, _ in results if "OK" in status)
print(f"✅ Funcionando: {ok_count}/{len(tests)}")
print(f"❌ Com erro: {len(tests) - ok_count}/{len(tests)}")

if ok_count == len(tests):
    print("\n🎉 TODAS AS VIEWS ESTÃO FUNCIONANDO!")
    print("O problema pode estar no navegador (cache) ou nas rotas.")
else:
    print("\n⚠️ VIEWS COM PROBLEMAS DETECTADOS")
    print("\n🔧 PRÓXIMOS PASSOS:")
    print("1. Verificar templates para erros de sintaxe")
    print("2. Verificar se há dados necessários no banco")
    print("3. Limpar cache do navegador")
