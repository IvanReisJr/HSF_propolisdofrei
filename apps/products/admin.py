# from django.contrib import admin
# from .models import Product, ProductStock, Packaging

# Removido do Admin conforme solicitação do usuário.
# Apenas Autenticação e Autorização devem aparecer no Django Admin.

# @admin.register(Packaging)
# class PackagingAdmin(admin.ModelAdmin):
#     list_display = ('name', 'is_active', 'created_at')
#     search_fields = ('name',)
#     list_filter = ('is_active',)

# class ProductStockInline(admin.TabularInline):
#     model = ProductStock
#     extra = 0
#     readonly_fields = ('updated_at',)

# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('code', 'name', 'category', 'packaging', 'unit', 'cost_price', 'sale_price', 'status', 'is_active')
#     list_filter = ('status', 'is_active', 'category', 'packaging')
#     search_fields = ('code', 'name', 'description')
#     inlines = [ProductStockInline]
#     fieldsets = (
#         ('Informações Básicas', {
#             'fields': ('code', 'name', 'description', 'category', 'packaging')
#         }),
#         ('Detalhes da Unidade', {
#             'fields': ('unit', 'unit_fk')
#         }),
#         ('Preços', {
#             'fields': ('cost_price', 'sale_price')
#         }),
#         ('Configurações', {
#             'fields': ('min_stock', 'status', 'is_active')
#         }),
#     )

# @admin.register(ProductStock)
# class ProductStockAdmin(admin.ModelAdmin):
#     list_display = ('product', 'establishment', 'current_stock', 'updated_at')
#     list_filter = ('establishment',)
#     search_fields = ('product__name', 'establishment__name')

