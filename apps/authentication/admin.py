from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Admin customizado para o modelo de usuário.
    Adiciona o campo distributor e suporte a filtros.
    """
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'avatar')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Organization'), {'fields': ('distributor',)}), # Novo campo
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('email', 'first_name', 'last_name', 'distributor')}),
    )
    
    list_display = ('email', 'username', 'first_name', 'last_name', 'distributor', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'distributor')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('email',)
