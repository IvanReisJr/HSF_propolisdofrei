from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, F, Count, DecimalField
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from apps.products.models import Product, ProductStock
from apps.orders.models import Order
from apps.stock.models import StockMovement
from apps.distributors.models import Distributor

@login_required
def dashboard(request):
    user = request.user
    # Alteração de escopo: User agora usa distributor, não establishment.
    # O middleware de simulação já pode ter alterado user.distributor
    distributor = getattr(user, 'distributor', None)
    
    # Data range for charts
    last_7_days = timezone.now() - timedelta(days=7)
    
    # Initialize data containers
    chart_data = {
        'movements_labels': [],
        'movements_values': [],
        'stock_labels': [],
        'stock_values': []
    }
    low_stock_items = []
    
    # Filtros baseados no distribuidor do usuário
    if user.is_super_user_role() and not getattr(request, 'is_simulating', False):
        # Admin global (sem simulação)
        total_products = Product.objects.filter(status='active').count()
        pending_orders = Order.objects.filter(status='pendente').count()
        recent_movements = StockMovement.objects.count() # Simplificado para 24h
        low_stock = ProductStock.objects.filter(current_stock__lt=10).count() # Exemplo
        recent_orders = Order.objects.all().order_by('-created_at')[:20] # Expanded for tab
        
        # Chart Data: Global
        # Stock Value by Category
        stock_value = ProductStock.objects.filter(current_stock__gt=0).values(
            'product__category__name'
        ).annotate(
            total_value=Sum(F('current_stock') * F('product__cost_price'))
        ).order_by('-total_value')
        
        # Movements (Last 7 days)
        movements = StockMovement.objects.filter(created_at__gte=last_7_days).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        # Low Stock List
        low_stock_qs = ProductStock.objects.filter(current_stock__lt=10).select_related('product', 'product__category', 'distributor')[:20]
        for item in low_stock_qs:
            low_stock_items.append({
                'name': item.product.name,
                'code': item.product.code,
                'category': item.product.category.name if item.product.category else '-',
                'distributor': item.distributor.name,
                'current_stock': item.current_stock,
                'id': item.product.id
            })
            
        # Latest Movements (Global)
        latest_stock_movements = StockMovement.objects.all().select_related('product', 'user', 'distributor').order_by('-created_at')[:10]

    else:
        if distributor:
            # Lógica para Matriz (Consolidado)
            if distributor.tipo_unidade == 'MATRIZ':
                matriz_distributors = Distributor.objects.filter(tipo_unidade='MATRIZ')
                
                # Estoque consolidado: conta produtos únicos com estoque na matriz
                # Somente conta produtos com estoque > 0 ou existentes na tabela de estoque
                total_products = ProductStock.objects.filter(
                    distributor__in=matriz_distributors, 
                    product__status='active',
                    current_stock__gt=0
                ).values('product').distinct().count()
                
                # Pedidos: Onde Matriz é origem ou destino
                pending_orders = Order.objects.filter(
                    Q(distributor__in=matriz_distributors) | Q(target_distributor__in=matriz_distributors), 
                    status='pendente'
                ).count()
                
                recent_movements = StockMovement.objects.filter(distributor__in=matriz_distributors).count()
                
                # Baixo estoque (Agregado por produto para considerar soma de lotes)
                low_stock_qs = ProductStock.objects.filter(
                    distributor__in=matriz_distributors,
                    product__status='active'
                ).values('product').annotate(
                    total_stock=Sum('current_stock')
                ).filter(total_stock__lt=10)
                
                low_stock = low_stock_qs.count()
                
                # Fetch actual products for Low Stock List (complex due to aggregation)
                low_stock_map = {item['product']: item['total_stock'] for item in low_stock_qs}
                products = Product.objects.filter(id__in=low_stock_map.keys()).select_related('category')[:20]
                
                for p in products:
                     low_stock_items.append({
                        'name': p.name,
                        'code': p.code,
                        'category': p.category.name if p.category else '-',
                        'distributor': 'Matriz (Consolidado)',
                        'current_stock': low_stock_map.get(p.id, 0),
                        'id': p.id
                    })
                
                recent_orders = Order.objects.filter(
                    Q(distributor__in=matriz_distributors) | Q(target_distributor__in=matriz_distributors)
                ).order_by('-created_at')[:20]
                
                # Chart Data: Matriz
                stock_value = ProductStock.objects.filter(
                    distributor__in=matriz_distributors,
                    current_stock__gt=0
                ).values(
                    'product__category__name'
                ).annotate(
                    total_value=Sum(F('current_stock') * F('product__cost_price'), output_field=DecimalField())
                ).order_by('-total_value')
                
                movements = StockMovement.objects.filter(
                    distributor__in=matriz_distributors,
                    created_at__gte=last_7_days
                ).annotate(
                    day=TruncDate('created_at')
                ).values('day').annotate(count=Count('id')).order_by('day')

                # Latest Movements (Matriz)
                latest_stock_movements = StockMovement.objects.filter(
                    distributor__in=matriz_distributors
                ).select_related('product', 'user', 'distributor').order_by('-created_at')[:10]

            # Lógica para Filial (Individual)
            else:
                total_products = ProductStock.objects.filter(
                    distributor=distributor, 
                    product__status='active',
                    current_stock__gt=0
                ).values('product').distinct().count()
                
                # Pedidos: Onde sou origem (Matriz) ou destino (Filial)
                pending_orders = Order.objects.filter(
                    Q(distributor=distributor) | Q(target_distributor=distributor), 
                    status='pendente'
                ).count()
                
                recent_movements = StockMovement.objects.filter(distributor=distributor).count()
                
                low_stock = ProductStock.objects.filter(
                    distributor=distributor, 
                    product__status='active'
                ).values('product').annotate(
                    total_stock=Sum('current_stock')
                ).filter(total_stock__lt=10).count()
                
                low_stock_items_qs = ProductStock.objects.filter(
                    distributor=distributor,
                    current_stock__lt=10
                ).select_related('product', 'product__category')[:20]
                
                for item in low_stock_items_qs:
                    low_stock_items.append({
                        'name': item.product.name,
                        'code': item.product.code,
                        'category': item.product.category.name if item.product.category else '-',
                        'distributor': item.distributor.name,
                        'current_stock': item.current_stock,
                        'id': item.product.id
                    })
                
                recent_orders = Order.objects.filter(
                    Q(distributor=distributor) | Q(target_distributor=distributor)
                ).order_by('-created_at')[:20]
                
                # Chart Data: Filial
                stock_value = ProductStock.objects.filter(
                    distributor=distributor,
                    current_stock__gt=0
                ).values(
                    'product__category__name'
                ).annotate(
                    total_value=Sum(F('current_stock') * F('product__cost_price'), output_field=DecimalField())
                ).order_by('-total_value')
                
                movements = StockMovement.objects.filter(
                    distributor=distributor,
                    created_at__gte=last_7_days
                ).annotate(
                    day=TruncDate('created_at')
                ).values('day').annotate(count=Count('id')).order_by('day')
                
                # Latest Movements (Filial)
                latest_stock_movements = StockMovement.objects.filter(
                    distributor=distributor
                ).select_related('product', 'user', 'distributor').order_by('-created_at')[:10]
                
        else:
            # Fallback seguro caso usuário não tenha distribuidor
            total_products = 0 
            pending_orders = 0
            recent_movements = 0
            low_stock = 0
            recent_orders = []
            stock_value = []
            movements = []
            low_stock_items = []
            latest_stock_movements = []

    # Process Chart Data
    if 'stock_value' in locals():
        for item in stock_value:
            cat_name = item['product__category__name'] or 'Sem Categoria'
            chart_data['stock_labels'].append(cat_name)
            chart_data['stock_values'].append(float(item['total_value'] or 0))
            
    if 'movements' in locals():
        for item in movements:
            chart_data['movements_labels'].append(item['day'].strftime('%d/%m'))
            chart_data['movements_values'].append(item['count'])

    context = {
        'stats': {
            'products_count': total_products,
            'pending_orders': pending_orders,
            'movements_count': recent_movements,
            'low_stock_count': low_stock,
        },
        'recent_orders': recent_orders,
        'low_stock_items': low_stock_items,
        'latest_stock_movements': latest_stock_movements,
        'distributor': distributor, # Para exibir no template qual visão está ativa
        'chart_data': chart_data,
    }
    return render(request, 'dashboard.html', context)


@login_required
def htmx_load_movements(request):
    user = request.user
    distributor = getattr(user, 'distributor', None)
    latest_stock_movements = []

    if user.is_super_user_role() and not getattr(request, 'is_simulating', False):
        latest_stock_movements = StockMovement.objects.all().select_related('product', 'user', 'distributor').order_by('-created_at')[:10]
    elif distributor:
        if distributor.tipo_unidade == 'MATRIZ':
            matriz_distributors = Distributor.objects.filter(tipo_unidade='MATRIZ')
            latest_stock_movements = StockMovement.objects.filter(
                distributor__in=matriz_distributors
            ).select_related('product', 'user', 'distributor').order_by('-created_at')[:10]
        else: # Filial
            latest_stock_movements = StockMovement.objects.filter(
                distributor=distributor
            ).select_related('product', 'user', 'distributor').order_by('-created_at')[:10]

    # Simula um pequeno atraso para que o skeleton loader seja visível
    import time
    time.sleep(0.5)

    context = {
        'latest_stock_movements': latest_stock_movements
    }
    return render(request, '_movement_table.html', context)

