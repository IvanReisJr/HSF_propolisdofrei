import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class AppRole(models.TextChoices):
    """Roles do sistema"""
    ADMIN = 'admin', _('Administrador')
    ESTOQUE = 'estoque', _('Estoque')
    VENDAS = 'vendas', _('Vendas')
    FINANCEIRO = 'financeiro', _('Financeiro')
    AUDITORIA = 'auditoria', _('Auditoria')


class User(AbstractUser):
    """
    Modelo de usuário customizado.
    Estende AbstractUser do Django para adicionar campos personalizados.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('E-mail'), unique=True)
    phone = models.CharField(_('Telefone'), max_length=20, blank=True, null=True)
    avatar = models.ImageField(_('Avatar'), upload_to='avatars/', blank=True, null=True)
    
    # Relacionamento com estabelecimento
    # Super usuário pode ver todos, usuários normais veem apenas seu estabelecimento
    establishment = models.ForeignKey(
        'establishments.Establishment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Estabelecimento'),
        related_name='users',
        help_text=_('Estabelecimento ao qual o usuário pertence. Deixe vazio para super usuário.')
    )
    
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def is_super_user_role(self):
        """Verifica se é super usuário (sem estabelecimento vinculado)"""
        return self.is_superuser or self.establishment is None


class UserRole(models.Model):
    """
    Modelo para armazenar roles dos usuários.
    Um usuário pode ter múltiplos roles.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='roles',
        verbose_name=_('Usuário')
    )
    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=AppRole.choices
    )
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)

    class Meta:
        db_table = 'user_roles'
        verbose_name = _('Role de Usuário')
        verbose_name_plural = _('Roles de Usuários')
        unique_together = ['user', 'role']

    def __str__(self):
        return f"{self.user.email} - {self.get_role_display()}"
