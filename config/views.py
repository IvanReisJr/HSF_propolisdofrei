from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.products.models import Product, ProductStock
from apps.orders.models import Order
from apps.stock.models import StockMovement

@login_required
def dashboard(request):
    user = request.user
    # Alteração de escopo: User agora usa distributor, não establishment.
    distributor = getattr(user, 'distributor', None)
    
    # Filtros baseados no distribuidor do usuário
    if user.is_super_user_role():
        total_products = Product.objects.filter(status='active').count()
        pending_orders = Order.objects.filter(status='pendente').count()
        recent_movements = StockMovement.objects.count() # Simplificado para 24h
        low_stock = ProductStock.objects.filter(current_stock__lt=10).count() # Exemplo
        recent_orders = Order.objects.all()[:5]
    else:
        # TODO: Atualizar lógica quando ProductStock e Order forem migrados para usar Distributor.
        # Por enquanto, retornamos 0 ou lista vazia para evitar erro de atributo.
        total_products = 0 
        pending_orders = 0
        recent_movements = 0
        low_stock = 0
        recent_orders = []
        
        # Código comentado aguardando refatoração de Estoque/Pedidos (Próxima Fase)
        # total_products = ProductStock.objects.filter(establishment=establishment, product__status='active').count()
        # pending_orders = Order.objects.filter(establishment=establishment, status='pendente').count()
        # recent_movements = StockMovement.objects.filter(establishment=establishment).count()
        # low_stock = ProductStock.objects.filter(establishment=establishment, current_stock__lt=10).count()
        # recent_orders = Order.objects.filter(establishment=establishment)[:5]

    context = {
        'stats': {
            'products_count': total_products,
            'pending_orders': pending_orders,
            'movements_count': recent_movements,
            'low_stock_count': low_stock,
        },
        'recent_orders': recent_orders,
    }
    return render(request, 'dashboard.html', context)
