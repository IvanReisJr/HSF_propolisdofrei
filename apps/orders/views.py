from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order, OrderItem
from apps.products.models import Product, ProductStock
from apps.distributors.models import Distributor
from apps.establishments.models import Establishment
from apps.stock.models import StockMovement
from django.db import transaction

@login_required
def order_list(request):
    user = request.user
    status_filter = request.GET.get('status', 'all')
    
    if user.is_super_user_role():
        orders = Order.objects.all()
    else:
        orders = Order.objects.filter(establishment=user.establishment)
    
    # Apply status filter
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    orders = orders.order_by('-created_at')
    
    context = {
        'orders': orders,
        'status_filter': status_filter
    }
    return render(request, 'orders/order_list.html', context)

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    context = {'order': order}
    return render(request, 'orders/order_detail.html', context)

@login_required
def order_create(request):
    print("DEBUG: Entered order_create view")
    if request.method == 'POST':
        print(f"DEBUG: POST data: {request.POST}")
        distributor_id = request.POST.get('distributor')
        establishment_id = request.POST.get('establishment')
        
        # Simple JSON-like processing from form (simplified for monolith)
        # In a real app we'd use Formsets or HTMX to add lines
        product_ids = request.POST.getlist('products[]')
        quantities = request.POST.getlist('quantities[]')
        unit_prices = request.POST.getlist('unit_prices[]')
        
        if not product_ids:
            messages.error(request, 'Adicione pelo menos um produto ao pedido.')
            return redirect('order_create')

        try:
            with transaction.atomic():
                distributor = get_object_or_404(Distributor, id=distributor_id)
                order = Order.objects.create(
                    establishment_id=establishment_id,
                    distributor=distributor,
                    user=request.user,  # Required: user who created the order
                    status='pendente',
                    total_amount=0 # Will update
                )
                
                total = 0
                for pid, qty, u_price in zip(product_ids, quantities, unit_prices):
                    if not qty or int(qty) <= 0: continue
                    
                    product = get_object_or_404(Product, id=pid)
                    qty = int(qty)
                    
                    # Convert localized string "1.200,50" to float
                    try:
                        clean_price = u_price.replace('.', '').replace(',', '.')
                        price = float(clean_price)
                    except ValueError:
                        price = product.sale_price
                        
                    subtotal = price * qty
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        unit_price=price,
                        total_price=subtotal
                    )
                    total += subtotal
                
                order.total_amount = total
                order.save()
                
                messages.success(request, f'Pedido {order.order_number} criado!')
                return redirect('order_detail', pk=order.pk)
        except Exception as e:
            messages.error(request, f'Erro ao criar pedido: {str(e)}')
            
    distributors = Distributor.objects.all()
    products = Product.objects.filter(status='active')
    
    # Enable selection of origin establishment
    if request.user.is_super_user_role():
        establishments = Establishment.objects.filter(is_active=True)
    else:
        # Check if user has establishment assigned
        if hasattr(request.user, 'establishment') and request.user.establishment:
            establishments = Establishment.objects.filter(id=request.user.establishment.id)
        else:
            # Fallback for headless users (should not happen in prod for normal roles)
            establishments = Establishment.objects.none()
        
    context = {
        'distributors': distributors,
        'products': products,
        'establishments': establishments
    }
    return render(request, 'orders/order_form.html', context)

@login_required
def order_confirm(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status != 'pendente':
        messages.error(request, 'Este pedido não pode ser confirmado.')
        return redirect('order_detail', pk=pk)
        
    try:
        with transaction.atomic():
            for item in order.items.all():
                # Check stock and deduct
                stock = ProductStock.objects.get(product=item.product, establishment=order.establishment)
                if stock.current_stock < item.quantity:
                    raise Exception(f'Estoque insuficiente para {item.product.name}')
                
                stock.current_stock -= item.quantity
                stock.save()
                
                # Record movement
                StockMovement.objects.create(
                    product=item.product,
                    establishment=order.establishment,
                    user=request.user,
                    type='exit',
                    quantity=item.quantity,
                    reason=f'Pedido {order.order_number} confirmado'
                )
            
            order.status = 'confirmado'
            order.save()
            messages.success(request, f'Pedido {order.order_number} confirmado e estoque atualizado!')
    except Exception as e:
        messages.error(request, str(e))
        
    return redirect('order_detail', pk=pk)

@login_required
def order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status != 'pendente':
        messages.error(request, 'Apenas pedidos pendentes podem ser cancelados.')
    else:
        order.status = 'cancelado'
        order.save()
        messages.success(request, 'Pedido cancelado.')
    return redirect('order_detail', pk=pk)

@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    # Restrict deletion to pending or canceled orders
    if order.status not in ['pendente', 'cancelado']:
        messages.error(request, 'Apenas pedidos pendentes ou cancelados podem ser excluídos.')
        return redirect('order_detail', pk=pk)
        
    if request.method == 'POST':
        order_number = order.order_number
        order.delete()
        messages.success(request, f'Pedido {order_number} excluído com sucesso.')
        return redirect('order_list')
        
    context = {'order': order}
    return render(request, 'orders/order_confirm_delete.html', context)
