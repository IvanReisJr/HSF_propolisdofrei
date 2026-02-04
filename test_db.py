import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.categories.models import Category
from apps.core.models import UnitOfMeasure
from apps.products.models import Packaging

print(f"Categories: {Category.objects.count()}")
print(f"Units: {UnitOfMeasure.objects.count()}")
print(f"Packagings: {Packaging.objects.count()}")
