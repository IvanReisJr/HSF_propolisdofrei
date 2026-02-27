import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.stock.models import StockMovement
from apps.products.models import ProductStock
from apps.orders.models import Order, OrderItem
from apps.audit.models import AuditLog

# 1. Soft delete em Movimentações
movements = StockMovement.objects.all()
count_mov = movements.count()
movements.update(is_active=False)
print(f"Inativados {count_mov} StockMovements.")

# 2. Soft delete em Pedidos e Itens
orders = Order.objects.all()
count_ord = orders.count()
orders.update(is_active=False)

items = OrderItem.objects.all()
count_items = items.count()
items.update(is_active=False)
print(f"Inativados {count_ord} Orders e {count_items} OrderItems.")

# 3. Zerar Estoque Atual
stocks = ProductStock.objects.all()
count_stocks = stocks.count()
stocks.update(current_stock=0)
print(f"Zerados saldos em {count_stocks} ProductStocks.")

# Opcional: Apagar log de auditoria antigo para limpar poluição no teste?
# Como o usuário quer depurar auditoria em branco, pode ser útil
count_audit = AuditLog.objects.count()
AuditLog.objects.all().delete()
print(f"Removidos {count_audit} Logs de Auditoria para iniciar teste limpo.")

print("Base de dados preparada com sucesso para rodar scripts de teste limpos!")
