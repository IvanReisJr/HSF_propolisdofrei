"""
Signals para o app de estoque.
Gera automaticamente entradas no AuditLog sempre que um StockMovement é criado.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StockMovement
from apps.audit.models import AuditLog


@receiver(post_save, sender=StockMovement)
def log_stock_movement(sender, instance, created, **kwargs):
    """
    Cria um registro no AuditLog sempre que um StockMovement é salvo.
    Se created=True, a ação é INSERT. Caso contrário, é UPDATE.
    """
    action = "INSERT" if created else "UPDATE"
    AuditLog.objects.create(
        user=instance.user,
        action=action,
        table_name="stock_movements",
        record_id=instance.id,
        new_data={
            "product": str(instance.product_id),
            "distributor": str(instance.distributor_id) if instance.distributor_id else None,
            "movement_type": instance.movement_type,
            "quantity": instance.quantity,
            "batch": instance.batch,
            "reason": instance.reason,
        }
    )
