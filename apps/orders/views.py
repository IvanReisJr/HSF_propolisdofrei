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
        # Filter by Target Distributor (The Filial)
        if hasattr(request.user, 'distributor') and request.user.distributor:
            orders = Order.objects.filter(target_distributor=request.user.distributor)
        else:
            orders = Order.objects.none()
    
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
    if request.method == 'POST':
        distributor_id = request.POST.get('distributor')
        establishment_id = request.POST.get('establishment')
        
        product_ids = request.POST.getlist('products[]')
        quantities = request.POST.getlist('quantities[]')
        unit_prices = request.POST.getlist('unit_prices[]')
        
        if not product_ids:
            messages.error(request, 'Adicione pelo menos um produto ao pedido.')
            return redirect('order_create')

        try:
            with transaction.atomic():
                # Isolation: Use user's distributor AS TARGET (Requester)
                target_distributor = getattr(request.user, 'distributor', None)
                
                # Source Distributor (Supplying CD) comes from Form
                if not distributor_id:
                    raise Exception("Selecione o Centro de Distribuição (Matriz).")
                
                source_distributor = get_object_or_404(Distributor, id=distributor_id)
                
                # Validation: Cannot order from self if self is Matriz? Or just allow?
                # Prompt says: "Garanta que uma Filial não consiga 'escolher' outra Filial como origem"
                # Filter in context ensures only MATRIZ are shown, but backend check is good.
                if getattr(source_distributor, 'tipo_unidade', '') != 'MATRIZ':
                    raise Exception("A origem deve ser uma MATRIZ.")

                order = Order.objects.create(
                    establishment_id=establishment_id, # Nullable or Legacy
                    distributor=source_distributor,    # Source
                    target_distributor=target_distributor, # Target
                    user=request.user,
                    status='pendente',
                    total_amount=0
                )
                
                total = 0
                for pid, qty, u_price in zip(product_ids, quantities, unit_prices):
                    if not qty or int(qty) <= 0: continue
                    
                    product = get_object_or_404(Product, id=pid)
                    
                    # SECURITY: Block inactive products
                    if not product.is_active:
                        raise Exception(f'Produto {product.name} está inativo e não pode ser incluído.')

                    qty = int(qty)
                    
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
            return redirect('order_create')
            
    # Distributors: Show ONLY MATRIZ options for source selection
    distributors = Distributor.objects.filter(tipo_unidade='MATRIZ', is_active=True)
    # SECURITY: Filter only active products
    products = Product.objects.filter(is_active=True)
    if request.user.distributor:
         # Show all active products available (Global catalog or restricted?)
         # Usually Filial can order any active product from Matriz.
         # So we list all active products.
         pass

    if request.user.is_super_user_role():
        establishments = Establishment.objects.filter(is_active=True)
    else:
        if hasattr(request.user, 'establishment') and request.user.establishment:
            establishments = Establishment.objects.filter(id=request.user.establishment.id)
        else:
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
                quantity_to_deduct = item.quantity
                product = item.product
                
                # Determine Distributor (Context of Stock Out)
                # If Order has a distributor, use it. Else fallback to user's?
                # Assuming Order.distributor is the SOURCE of the goods (Seller) or TARGET?
                # Usually Order.distributor is the entity PLACING the order in this model?
                # IF this is a Sales Order, we deduct from established source.
                # FOR SIMULATION: We assume we are deducting from the Order's associated Distributor.
                distributor = order.distributor 
                if not distributor:
                     raise Exception("Pedido sem Distribuidor vinculado. Não é possível baixar estoque.")

                # FIFO Strategy: Operations on (Distributor + Product), ordered by Expiry
                stocks = ProductStock.objects.filter(
                    product=product, 
                    distributor=distributor,
                    current_stock__gt=0
                ).order_by('expiration_date', 'created_at') # First expiring first
                
                total_available = sum(s.current_stock for s in stocks)
                
                if total_available < quantity_to_deduct:
                    raise Exception(f'Estoque insuficiente para {product.name}. Disponível: {total_available}')
                
                for stock in stocks:
                    if quantity_to_deduct <= 0:
                        break
                        
                    deduct = min(stock.current_stock, quantity_to_deduct)
                    previous_stock = stock.current_stock
                    stock.current_stock -= deduct
                    stock.save()
                    
                    quantity_to_deduct -= deduct
                    
                    # Record movement for this batch portion
                    StockMovement.objects.create(
                        product=product,
                        distributor=distributor,
                        user=request.user,
                        movement_type='exit',
                        quantity=deduct,
                        reason=f'Pedido {order.order_number} confirmado',
                        batch=stock.batch,
                        expiration_date=stock.expiration_date,
                        previous_stock=previous_stock,
                        new_stock=stock.current_stock,
                        reference_id=order.id,
                        reference_type='order'
                    )
            
            order.status = 'confirmado'
            order.save()
            messages.success(request, f'Pedido {order.order_number} confirmado e estoque baixado (MPVS)!')
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
