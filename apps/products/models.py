import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class ProductStatus(models.TextChoices):
    """Status do produto"""
    ACTIVE = 'active', _('Ativo')
    INACTIVE = 'inactive', _('Inativo')


class Product(models.Model):
    """
    Modelo para produtos.
    Cada produto tem estoque por estabelecimento (via ProductStock).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(_('Código'), max_length=50, unique=True)
    name = models.CharField(_('Nome'), max_length=200)
    description = models.TextField(_('Descrição'), blank=True, null=True)
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Categoria'),
        related_name='products'
    )
    unit = models.CharField(
        _('Unidade'),
        max_length=10,
        default='un',
        help_text=_('Unidade de medida (un, kg, l, etc.)')
    )
    cost_price = models.DecimalField(
        _('Preço de Custo'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    sale_price = models.DecimalField(
        _('Preço de Venda'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    min_stock = models.IntegerField(
        _('Estoque Mínimo'),
        default=0,
        help_text=_('Estoque mínimo para alerta')
    )
    status = models.CharField(
        _('Status'),
        max_length=10,
        choices=ProductStatus.choices,
        default=ProductStatus.ACTIVE
    )
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        db_table = 'products'
        verbose_name = _('Produto')
        verbose_name_plural = _('Produtos')
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_total_stock(self):
        """Retorna estoque total em todos os estabelecimentos"""
        return self.stocks.aggregate(
            total=models.Sum('current_stock')
        )['total'] or 0

    def get_stock_by_establishment(self, establishment):
        """Retorna estoque de um estabelecimento específico"""
        try:
            stock = self.stocks.get(establishment=establishment)
            return stock.current_stock
        except ProductStock.DoesNotExist:
            return 0

    def get_margin(self):
        """Calcula a margem de lucro percentual"""
        if self.cost_price and self.cost_price > 0:
            margin = ((self.sale_price - self.cost_price) / self.cost_price) * 100
            return float(margin)
        return 0.0


class ProductStock(models.Model):
    """
    Estoque de produto por estabelecimento.
    Cada produto tem um registro de estoque para cada estabelecimento.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stocks',
        verbose_name=_('Produto')
    )
    establishment = models.ForeignKey(
        'establishments.Establishment',
        on_delete=models.CASCADE,
        related_name='product_stocks',
        verbose_name=_('Estabelecimento')
    )
    current_stock = models.IntegerField(_('Estoque Atual'), default=0)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        db_table = 'product_stocks'
        verbose_name = _('Estoque de Produto')
        verbose_name_plural = _('Estoques de Produtos')
        unique_together = ['product', 'establishment']

    def __str__(self):
        return f"{self.product.name} - {self.establishment.name}: {self.current_stock}"
