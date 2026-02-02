import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class Establishment(models.Model):
    """
    Modelo para representar unidades/estabelecimentos.
    Exemplos: Taubaté, Rio de Janeiro, Campos, Jaci, Belo Horizonte
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        _('Código'),
        max_length=20,
        unique=True,
        help_text=_('Código único do estabelecimento (ex: TAU, RJ, CAM)')
    )
    name = models.CharField(
        _('Nome'),
        max_length=200,
        help_text=_('Nome do estabelecimento (ex: Taubaté, Rio de Janeiro)')
    )
    city = models.CharField(_('Cidade'), max_length=100)
    state = models.CharField(_('Estado'), max_length=2)
    address = models.TextField(_('Endereço'), blank=True, null=True)
    phone = models.CharField(_('Telefone'), max_length=20, blank=True, null=True)
    email = models.EmailField(_('E-mail'), blank=True, null=True)
    is_active = models.BooleanField(_('Ativo'), default=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        db_table = 'establishments'
        verbose_name = _('Estabelecimento')
        verbose_name_plural = _('Estabelecimentos')
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"
