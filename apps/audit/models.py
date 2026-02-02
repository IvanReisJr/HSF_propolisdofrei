import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditLog(models.Model):
    """
    Modelo para logs de auditoria.
    Registra todas as operações importantes do sistema.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('Usuário')
    )
    action = models.CharField(
        _('Ação'),
        max_length=20,
        help_text=_('INSERT, UPDATE, DELETE')
    )
    table_name = models.CharField(_('Tabela'), max_length=100)
    record_id = models.UUIDField(_('ID do Registro'), null=True, blank=True)
    old_data = models.JSONField(_('Dados Antigos'), null=True, blank=True)
    new_data = models.JSONField(_('Dados Novos'), null=True, blank=True)
    ip_address = models.GenericIPAddressField(_('Endereço IP'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), null=True, blank=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        verbose_name = _('Log de Auditoria')
        verbose_name_plural = _('Logs de Auditoria')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['table_name']),
        ]

    def __str__(self):
        user_email = self.user.email if self.user else 'Sistema'
        return f"{self.action} - {self.table_name} - {user_email}"
