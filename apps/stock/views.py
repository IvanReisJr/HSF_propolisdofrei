from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import StockMovement
from apps.products.models import Product, ProductStock
from apps.establishments.models import Establishment

@login_required
def movement_list(request):
    user = request.user
    if user.is_super_user_role():
        movements = StockMovement.objects.all().order_by('-created_at')
    else:
        movements = StockMovement.objects.filter(establishment=user.establishment).order_by('-created_at')
    
    context = {'movements': movements}
    return render(request, 'stock/movement_list.html', context)

@login_required
def movement_create(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        establishment_id = request.POST.get('establishment')
        movement_type = request.POST.get('type')
        quantity = int(request.POST.get('quantity'))
        reason = request.POST.get('reason')
        
        product = get_object_or_404(Product, id=product_id)
        establishment = get_object_or_404(Establishment, id=establishment_id)
        
        # Validation and Stock update logic usually would be in a service/manager
        # For now, implemented here for simplicity
        stock, created = ProductStock.objects.get_or_create(
            product=product, establishment=establishment, defaults={'current_stock': 0}
        )
        
        if movement_type in ['entry', 'adjustment_plus', 'reversal_out']:
            stock.current_stock += quantity
        else:
            if stock.current_stock < quantity and movement_type not in ['adjustment_minus']:
                messages.error(request, 'Estoque insuficiente para esta operação.')
                return redirect('movement_create')
            stock.current_stock -= quantity
            
        stock.save()
        
        StockMovement.objects.create(
            product=product,
            establishment=establishment,
            user=request.user,
            movement_type=movement_type,
            quantity=quantity,
            previous_stock=stock.current_stock - quantity if movement_type in ['saida', 'adjustment_minus'] else stock.current_stock,
            new_stock=stock.current_stock,
            reason=reason
        )
        
        messages.success(request, f'Movimentação de {quantity} {product.unit} registrada com sucesso.')
        return redirect('movement_list')
        
    products = Product.objects.filter(status='active')
    # If not superuser, limited to their establishment
    if request.user.is_super_user_role():
        establishments = Establishment.objects.all()
    else:
        establishments = Establishment.objects.filter(id=request.user.establishment.id)
        
    context = {
        'products': products,
        'establishments': establishments
    }
    return render(request, 'stock/movement_form.html', context)

@login_required
def get_stock_level(request):
    product_id = request.GET.get('product')
    establishment_id = request.GET.get('establishment')
    
    if not product_id or not establishment_id:
        return render(request, 'stock/partials/stock_level.html', {'stock': None})
        
    try:
        stock = ProductStock.objects.filter(
            product_id=product_id, 
            establishment_id=establishment_id
        ).first()
        
        current_stock = stock.current_stock if stock else 0
        
        return render(request, 'stock/partials/stock_level.html', {'stock': current_stock})
    except Exception:
        return render(request, 'stock/partials/stock_level.html', {'stock': None})
