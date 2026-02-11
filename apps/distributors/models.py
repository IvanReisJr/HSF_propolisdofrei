import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.constants import BRAZIL_STATES


class DistributorType(models.TextChoices):
    """Tipos de distribuidor para controle de permissões"""
    HEADQUARTERS = 'headquarters', _('Matriz')
    BRANCH = 'branch', _('Filial')


class Distributor(models.Model):
    """
    Modelo para distribuidores/clientes internos.
    Representa unidades que recebem produtos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(_('Código'), max_length=50, unique=True, editable=False)
    name = models.CharField(_('Nome'), max_length=200)
    document = models.CharField(
        _('Documento'),
        max_length=20,
        blank=True,
        null=True,
        help_text=_('CNPJ/CPF')
    )
    email = models.EmailField(_('E-mail'), blank=True, null=True)
    phone = models.CharField(_('Telefone'), max_length=20, blank=True, null=True)
    address = models.TextField(_('Endereço'), blank=True, null=True)
    city = models.CharField(_('Cidade'), max_length=100, blank=True, null=True)
    state = models.CharField(_('Estado'), max_length=2, choices=BRAZIL_STATES, blank=True, null=True)
    notes = models.TextField(_('Observações'), blank=True, null=True)
    distributor_type = models.CharField(
        _('Tipo (Antigo)'),
        max_length=20,
        choices=DistributorType.choices,
        default=DistributorType.BRANCH,
        help_text=_('Mantido para compatibilidade')
    )
    
    class UnidadeType(models.TextChoices):
        MATRIZ = 'MATRIZ', _('Matriz / Fornecedor')
        FILIAL = 'FILIAL', _('Filial / Comprador')

    tipo_unidade = models.CharField(
        _('Tipo de Unidade'),
        max_length=10,
        choices=UnidadeType.choices,
        default=UnidadeType.FILIAL,
        help_text=_('Define se é Matriz ou Filial')
    )

    is_active = models.BooleanField(_('Ativo'), default=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        db_table = 'distributors'
        verbose_name = _('Unidade')
        verbose_name_plural = _('Unidades')
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.code:
            last_dist = Distributor.objects.order_by('-created_at').first()
            if last_dist and last_dist.code.startswith('DIST'):
                try:
                    last_num = int(last_dist.code.replace('DIST', ''))
                    self.code = f"DIST{last_num + 1:05d}"
                except ValueError:
                    # Fallback if code format is unexpected
                    count = Distributor.objects.count() + 1
                    self.code = f"DIST{count:05d}"
            else:
                count = Distributor.objects.count() + 1
                self.code = f"DIST{count:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"
