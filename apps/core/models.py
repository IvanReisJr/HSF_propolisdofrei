import uuid
from django.db import models
from django.db import transaction
from django.utils.translation import gettext_lazy as _

class UnitOfMeasure(models.Model):
    """Modelo para unidades de medida padronizadas"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Nome'), max_length=50, unique=True, help_text=_('Ex: Quilograma, Unidade, Metro'))
    abbreviation = models.CharField(_('Sigla'), max_length=10, unique=True, help_text=_('Ex: kg, un, m'))
    is_active = models.BooleanField(_('Ativo'), default=True)
    
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        db_table = 'units_of_measure'
        verbose_name = _('Unidade de Medida')
        verbose_name_plural = _('Unidades de Medida')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class Sequence(models.Model):
    """
    Modelo para controle de sequências numéricas atômicas.
    Garante unicidade em números de pedidos, notas, etc.
    """
    key = models.CharField(_('Chave da Sequência'), max_length=50, primary_key=True)
    value = models.PositiveIntegerField(_('Valor Atual'), default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sequences'
        verbose_name = _('Sequência')
        verbose_name_plural = _('Sequências')

    @classmethod
    def get_next_value(cls, key):
        """
        Retorna o próximo valor da sequência de forma atômica.
        Garante lock no registro para evitar condições de corrida.
        """
        with transaction.atomic():
            sequence, created = cls.objects.select_for_update().get_or_create(
                key=key,
                defaults={'value': 0}
            )
            sequence.value += 1
            sequence.save()
            return sequence.value
