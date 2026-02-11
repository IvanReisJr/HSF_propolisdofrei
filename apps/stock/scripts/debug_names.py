import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.products.models import Product
from apps.distributors.models import Distributor

print("--- Produtos Disponíveis ---")
for product in Product.objects.all():
    print(f"- {product.name}")

print("\n--- Unidades Disponíveis ---")
for distributor in Distributor.objects.all():
    print(f"- {distributor.name}")
