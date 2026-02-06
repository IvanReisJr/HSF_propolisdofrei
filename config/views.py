from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
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
        if distributor:
             # Lógica corrigida para usar Distributor
            total_products = ProductStock.objects.filter(distributor=distributor, product__status='active').count()
            
            # Pedidos: Onde sou origem (Matriz) ou destino (Filial)
            pending_orders = Order.objects.filter(
                Q(distributor=distributor) | Q(target_distributor=distributor), 
                status='pendente'
            ).count()
            
            recent_movements = StockMovement.objects.filter(distributor=distributor).count()
            
            low_stock = ProductStock.objects.filter(distributor=distributor, current_stock__lt=10).count()
            
            recent_orders = Order.objects.filter(
                Q(distributor=distributor) | Q(target_distributor=distributor)
            ).order_by('-created_at')[:5]
        else:
            # Fallback seguro caso usuário não tenha distribuidor
            total_products = 0 
            pending_orders = 0
            recent_movements = 0
            low_stock = 0
            recent_orders = []

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
