import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class ProductStatus(models.TextChoices):
    """Status do produto"""
    ACTIVE = 'active', _('Ativo')
    INACTIVE = 'inactive', _('Inativo')


class ActiveManager(models.Manager):
    """Manager para retornar apenas produtos não deletados"""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)



class Packaging(models.Model):
    """
    Modelo para tipos de embalagem (ex: Caixa, Frasco, Sachê).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Nome'), max_length=100, unique=True)
    is_active = models.BooleanField(_('Ativo'), default=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        db_table = 'packagings'
        verbose_name = _('Embalagem')
        verbose_name_plural = _('Embalagens')
        ordering = ['name']

    def __str__(self):
        return self.name


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
    packaging = models.ForeignKey(
        Packaging,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Embalagem'),
        related_name='products',
        help_text=_('Tipo de embalagem do produto')
    )
    distributor = models.ForeignKey(
        'distributors.Distributor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Matriz'),
        related_name='products',
        help_text=_('Matriz proprietária deste produto')
    )
    unit = models.CharField(
        _('Unidade'),
        max_length=10,
        default='un',
        help_text=_('Unidade de medida (un, kg, l, etc.)')
    )
    unit_fk = models.ForeignKey(
        'core.UnitOfMeasure',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Unidade (Normalizada)'),
        related_name='products'
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
    
    # Soft Delete
    is_active = models.BooleanField(_('Ativo (Soft Delete)'), default=True)
    
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    # Managers
    objects = ActiveManager()    # Default manager returns only active
    all_objects = models.Manager() # Returns everything including deleted

    class Meta:
        db_table = 'products'
        verbose_name = _('Produto')
        verbose_name_plural = _('Produtos')
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"
        
    def delete(self, using=None, keep_parents=False):
        """Soft delete: apenas marca como inativo"""
        self.is_active = False
        self.save()

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
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'establishment'],
                name='unique_product_establishment'
            )
        ]

    def __str__(self):
        return f"{self.product.name} - {self.establishment.name}: {self.current_stock}"
