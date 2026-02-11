from django.contrib import admin
from .models import Distributor

@admin.register(Distributor)
class DistributorAdmin(admin.ModelAdmin):
    # Alterando título da seção no Admin
    verbose_name_plural = 'Gestão de Unidades'
    
    list_display = ('code', 'name', 'phone', 'city', 'state', 'tipo_unidade', 'is_active')
    search_fields = ('code', 'name', 'document', 'city')
    list_filter = ('state', 'tipo_unidade', 'is_active')
    readonly_fields = ('code',)
    fieldsets = (
        ('Identificação', {
            'fields': ('code', 'name', 'document', 'tipo_unidade', 'is_active')
        }),
        ('Contato', {
            'fields': ('email', 'phone')
        }),
        ('Endereço', {
            'fields': ('address', 'city', 'state')
        }),
        ('Outros', {
            'fields': ('notes', 'distributor_type')
        }),
    )
