import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
from apps.core.models import Sequence  # Import Sequence
from django.utils.text import slugify


class OrderStatus(models.TextChoices):
    """Status do pedido"""
    PENDENTE = 'pendente', _('Pendente')
    AUTORIZADO = 'autorizado', _('Autorizado')
    CONFIRMADO = 'confirmado', _('Confirmado')
    CANCELADO = 'cancelado', _('Cancelado')
    ENTREGUE = 'entregue', _('Entregue')


class PaymentCondition(models.TextChoices):
    """Condição de Pagamento"""
    VISTA = 'vista', _('À Vista')
    PRAZO = 'prazo', _('À Prazo')
    CONSIGNADO = 'consignado', _('Consignado')
    DOACAO = 'doacao', _('Doação')


class PaymentStatus(models.TextChoices):
    """Status do Pagamento"""
    PENDENTE = 'pendente', _('Pendente')
    PARCIAL = 'parcial', _('Parcial')
    TOTAL = 'total', _('Total')
    ISENTO = 'isento', _('Isento')


class Order(models.Model):
    """
    Modelo para pedidos/distribuições internas.
    Vinculado a um estabelecimento específico.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(_('Número do Pedido'), max_length=50, unique=True)
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
    payment_condition = models.CharField(
        _('Condição de Pagamento'),
        max_length=20,
        choices=PaymentCondition.choices,
        default=PaymentCondition.VISTA
    )
    payment_status = models.CharField(
        _('Status do Pagamento'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDENTE
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
        return f"{self.order_number} - {self.distributor.name if self.distributor else 'N/A'}"
        
    @property
    def total_submitted(self):
        """Soma de todos os AccountSettlement (Pendentes + Validados)"""
        return self.settlements.aggregate(
            total=models.Sum('value_reported')
        )['total'] or Decimal('0.00')

    @property
    def total_confirmed(self):
        """Soma apenas dos AccountSettlement com is_validated=True"""
        return self.settlements.filter(is_validated=True).aggregate(
            total=models.Sum('value_reported')
        )['total'] or Decimal('0.00')
        
    @property
    def pending_balance(self):
        """Calcula o saldo devedor: Total - Total Enviado (para evitar duplicidade)"""
        return self.total_amount - self.total_submitted

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


def settlement_file_path(instance, filename):
    # media/prestacao_contas/[slug-da-filial]/[ANO]/[MES]/[DIA]/comprovante_pedido_[ID].ext
    ext = filename.split('.')[-1]
    distributor_slug = slugify(instance.order.target_distributor.name) if instance.order.target_distributor else 'geral'
    now = timezone.now()
    return f'prestacao_contas/{distributor_slug}/{now.year}/{now.month:02d}/{now.day:02d}/comprovante_pedido_{instance.order.id}.{ext}'


class AccountSettlement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='settlements',
        verbose_name=_('Pedido')
    )
    value_reported = models.DecimalField(
        _('Valor Informado'),
        max_digits=12,
        decimal_places=2
    )
    receipt_file = models.FileField(
        _('Comprovante'),
        upload_to=settlement_file_path
    )
    is_validated = models.BooleanField(
        _('Validado'),
        default=False
    )
    validated_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validated_settlements',
        verbose_name=_('Validado por')
    )
    rejection_reason = models.TextField(
        _('Motivo da Recusa'),
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_('Enviado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('Prestação de Conta')
        verbose_name_plural = _('Prestações de Contas')
        ordering = ['-created_at']

    def __str__(self):
        return f"Pagamento - {self.order.order_number}"
