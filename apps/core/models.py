import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _

class UnitOfMeasure(models.Model):
    """Modelo para unidades de medida padronizadas"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Nome'), max_length=50, unique=True, help_text=_('Ex: Quilograma, Unidade, Metro'))
    abbreviation = models.CharField(_('Sigla'), max_length=10, unique=True, help_text=_('Ex: kg, un, m'))
    
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        db_table = 'units_of_measure'
        verbose_name = _('Unidade de Medida')
        verbose_name_plural = _('Unidades de Medida')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"
