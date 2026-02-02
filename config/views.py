from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.products.models import Product, ProductStock
from apps.orders.models import Order
from apps.stock.models import StockMovement

@login_required
def dashboard(request):
    user = request.user
    establishment = user.establishment

    # Filtros baseados no estabelecimento do usuário
    if user.is_super_user_role():
        total_products = Product.objects.filter(status='active').count()
        pending_orders = Order.objects.filter(status='pendente').count()
        recent_movements = StockMovement.objects.count() # Simplificado para 24h
        low_stock = ProductStock.objects.filter(current_stock__lt=10).count() # Exemplo
        recent_orders = Order.objects.all()[:5]
    else:
        total_products = ProductStock.objects.filter(establishment=establishment, product__status='active').count()
        pending_orders = Order.objects.filter(establishment=establishment, status='pendente').count()
        recent_movements = StockMovement.objects.filter(establishment=establishment).count()
        low_stock = ProductStock.objects.filter(establishment=establishment, current_stock__lt=10).count()
        recent_orders = Order.objects.filter(establishment=establishment)[:5]

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
