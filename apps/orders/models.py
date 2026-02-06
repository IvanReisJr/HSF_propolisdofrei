import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
from apps.core.models import Sequence  # Import Sequence


class OrderStatus(models.TextChoices):
    """Status do pedido"""
    PENDENTE = 'pendente', _('Pendente')
    CONFIRMADO = 'confirmado', _('Confirmado')
    CANCELADO = 'cancelado', _('Cancelado')
    ENTREGUE = 'entregue', _('Entregue')


class Order(models.Model):
    """
    Modelo para pedidos/distribuições internas.
    Vinculado a um estabelecimento específico.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(_('Número do Pedido'), max_length=50, unique=True)
    establishment = models.ForeignKey(
        'establishments.Establishment',
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_('Estabelecimento (Legado)'),
        help_text=_('Campo legado. Use target_distributor.'),
        null=True,
        blank=True
    )
    distributor = models.ForeignKey(
        'distributors.Distributor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_orders',
        verbose_name=_('CD de Origem (Matriz)')
    )
    target_distributor = models.ForeignKey(
        'distributors.Distributor',
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name=_('Filial de Destino'),
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_('Usuário')
    )
    status = models.CharField(
        _('Status'),
        max_length=15,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDENTE
    )
    total_amount = models.DecimalField(
        _('Valor Total'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    notes = models.TextField(_('Observações'), blank=True, null=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        db_table = 'orders'
        verbose_name = _('Pedido')
        verbose_name_plural = _('Pedidos')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.establishment.name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Atomicamente obter o pŕoximo número sequencial do dia
            now = timezone.now()
            today_str = now.strftime('%Y%m%d')
            sequence_key = f'order_{today_str}'
            
            # Usar select_for_update via Sequence model
            seq_num = Sequence.get_next_value(sequence_key)
            
            # Formatar: PED-AAAAMMDD-XXXX
            self.order_number = f"PED-{today_str}-{seq_num:04d}"
                
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Itens do pedido"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Pedido')
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('Produto')
    )
    quantity = models.IntegerField(_('Quantidade'))
    unit_price = models.DecimalField(_('Preço Unitário'), max_digits=10, decimal_places=2)
    total_price = models.DecimalField(_('Preço Total'), max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)

    class Meta:
        db_table = 'order_items'
        verbose_name = _('Item do Pedido')
        verbose_name_plural = _('Itens do Pedido')

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

    def save(self, *args, **kwargs):
        """Calcula o total_price automaticamente"""
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
