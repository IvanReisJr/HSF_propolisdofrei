import os
import django
import sys

# Adicionar o diretório do projeto ao path
sys.path.append(r"C:\IvanReis\Sistemas_HSF\HSF_propolisdofrei")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.distributors.models import Distributor

try:
    print(f"Total distributors: {Distributor.objects.count()}")
    for d in Distributor.objects.all():
        print(f"ID: {d.id} | Code: {d.code} | Name: {d.name} | State: {d.state}")
except Exception as e:
    print(f"Error: {e}")
