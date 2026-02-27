import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class StockMovementType(models.TextChoices):
    """Tipos de movimentação de estoque"""
    ENTRY = 'entry', _('Entrada Manual')
    EXIT = 'exit', _('Saída Manual')
    ADJUSTMENT_PLUS = 'adjustment_plus', _('Ajuste (Adicionar)')
    ADJUSTMENT_MINUS = 'adjustment_minus', _('Ajuste (Subtrair)')
    REVERSAL_IN = 'reversal_in', _('Estorno de Entrada')
    REVERSAL_OUT = 'reversal_out', _('Estorno de Saída')
    TRANSFER_OUT = 'transfer_out', _('Saída por Transferência')
    TRANSFER_IN = 'transfer_in', _('Entrada por Transferência')


class StockMovement(models.Model):
    """
    Modelo para movimentações de estoque.
    Registra todas as entradas, saídas, ajustes e estornos por estabelecimento.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    distributor = models.ForeignKey(
        'distributors.Distributor',
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name=_('Distribuidor'),
        null=True,
        blank=True
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name=_('Produto')
    )
    movement_type = models.CharField(
        _('Tipo de Movimentação'),
        max_length=20,
        choices=StockMovementType.choices
    )
    quantity = models.IntegerField(_('Quantidade'))
    previous_stock = models.IntegerField(_('Estoque Anterior'))
    new_stock = models.IntegerField(_('Novo Estoque'))
    new_stock = models.IntegerField(_('Novo Estoque'))
    batch = models.CharField(_('Lote'), max_length=50, null=True, blank=True)
    expiration_date = models.DateField(_('Data de Validade'), null=True, blank=True)
    reason = models.TextField(_('Motivo'))
    reference_id = models.UUIDField(
        _('ID de Referência'),
        null=True,
        blank=True,
        help_text=_('ID do pedido ou outra referência')
    )
    reference_type = models.CharField(
        _('Tipo de Referência'),
        max_length=50,
        null=True,
        blank=True,
        help_text=_('order, transfer, adjustment, etc.')
    )
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name=_('Usuário')
    )
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)

    class Meta:
        db_table = 'stock_movements'
        verbose_name = _('Movimentação de Estoque')
        verbose_name_plural = _('Movimentações de Estoque')
        ordering = ['-created_at']

    def __str__(self):
        distributor_name = self.distributor.name if self.distributor else "N/A"
        return f"{self.get_movement_type_display()} - {self.product.name} - {distributor_name}"
