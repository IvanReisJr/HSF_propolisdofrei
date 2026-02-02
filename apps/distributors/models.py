import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class Distributor(models.Model):
    """
    Modelo para distribuidores/clientes internos.
    Representa unidades que recebem produtos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(_('Código'), max_length=50, unique=True)
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
    state = models.CharField(_('Estado'), max_length=2, blank=True, null=True)
    notes = models.TextField(_('Observações'), blank=True, null=True)
    is_active = models.BooleanField(_('Ativo'), default=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        db_table = 'distributors'
        verbose_name = _('Distribuidor')
        verbose_name_plural = _('Distribuidores')
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"
