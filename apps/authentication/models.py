import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom manager for User model to handle creation with email as username.
    """
    def create_user(self, email, username=None, password=None, **extra_fields):
        if not email:
            raise ValueError(_('O campo Email é obrigatório'))
        email = self.normalize_email(email)
        # Se username não for fornecido, usa o email
        if not username:
            username = email
            
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser precisa ter is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser precisa ter is_superuser=True.'))

        return self.create_user(email, username, password, **extra_fields)


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
    Estende AbstractUser do Django.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('E-mail'), unique=True)
    phone = models.CharField(_('Telefone'), max_length=20, blank=True, null=True)
    avatar = models.ImageField(_('Avatar'), upload_to='avatars/', blank=True, null=True)
    
    # Substituindo establishment por distributor
    distributor = models.ForeignKey(
        'distributors.Distributor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Distribuidor'),
        related_name='users',
        help_text=_('Distribuidor ao qual o usuário pertence. Obrigatório para usuários não administradores.')
    )
    
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    objects = CustomUserManager()

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

    def clean(self):
        super().clean()
        # Validação: Distribuidor é obrigatório para não-superusuários
        if not self.is_superuser and not self.distributor:
             raise ValidationError({
                'distributor': _('O campo Distribuidor é obrigatório para usuários comuns.')
            })

    def is_super_user_role(self):
        """Verifica se é super usuário (sem distribuidor vinculado)"""
        return self.is_superuser or self.distributor is None


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
