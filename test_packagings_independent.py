import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.products.views import packaging_list, packaging_create

User = get_user_model()

print("=" * 60)
print("🔍 TESTE: EMBALAGENS COMO CADASTRO INDEPENDENTE")
print("=" * 60)

user = User.objects.filter(is_superuser=True).first()
if not user:
    print("❌ Nenhum superusuário encontrado!")
    exit(1)

print(f"✅ Usuário de teste: {user.email}\n")

factory = RequestFactory()

tests = [
    (packaging_list, "/packagings/", "Lista de Embalagens"),
    (packaging_create, "/packagings/new/", "Nova Embalagem"),
]

print("📋 TESTANDO ROTAS INDEPENDENTES:")
print("-" * 60)

all_ok = True
for view_func, url, name in tests:
    try:
        request = factory.get(url)
        request.user = user
        response = view_func(request)
        
        if response.status_code == 200:
            print(f"✅ {name:30} HTTP 200")
        else:
            print(f"❌ {name:30} HTTP {response.status_code}")
            all_ok = False
    except Exception as e:
        print(f"❌ {name:30} ERRO: {str(e)[:60]}")
        all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("🎉 SUCESSO! Embalagens agora é um cadastro independente!")
    print("\n📍 Novas URLs:")
    print("   - /packagings/")
    print("   - /packagings/new/")
    print("   - /packagings/<id>/edit/")
else:
    print("⚠️ Alguns testes falharam. Verifique os erros acima.")
print("=" * 60)
