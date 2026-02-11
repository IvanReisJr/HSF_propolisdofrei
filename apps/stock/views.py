from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from .models import StockMovement, StockMovementType
from apps.products.models import Product, ProductStock
from apps.distributors.models import Distributor

def get_stock_distributor(user):
    """
    Returns the distributor to be used for stock operations.
    If user's distributor is MATRIZ, returns the primary MATRIZ distributor.
    Otherwise returns user's distributor.
    """
    if not hasattr(user, 'distributor') or not user.distributor:
        return None
        
    if user.distributor.tipo_unidade == 'MATRIZ':
        # Find the primary Matriz (e.g., the first one created)
        # Strategy: Use the one with oldest created_at as the "Master"
        primary = Distributor.objects.filter(tipo_unidade='MATRIZ').order_by('created_at').first()
        return primary if primary else user.distributor
    
    return user.distributor

@login_required
def movement_list(request):
    movements = StockMovement.objects.all().select_related('product', 'distributor', 'user').order_by('-created_at')
    
    if not request.user.is_superuser:
        distributor = get_stock_distributor(request.user)
        if distributor:
             if distributor.tipo_unidade == 'MATRIZ':
                 matriz_distributors = Distributor.objects.filter(tipo_unidade='MATRIZ')
                 movements = movements.filter(distributor__in=matriz_distributors)
             else:
                 movements = movements.filter(distributor=distributor)
        
    return render(request, 'stock/movement_list.html', {'movements': movements})

@login_required
@transaction.atomic
def movement_create(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        distributor_id = request.POST.get('distributor')
        movement_type = request.POST.get('type')
        try:
            quantity = int(request.POST.get('quantity') or 0)
        except ValueError:
            quantity = 0
        reason = request.POST.get('reason')

        if not all([product_id, distributor_id, movement_type]) or quantity <= 0:
            messages.error(request, 'Preencha todos os campos corretamente.')
            return redirect('movement_create')

        target_distributor = Distributor.objects.get(id=distributor_id)
        if target_distributor.tipo_unidade == 'MATRIZ':
            target_distributor = Distributor.objects.filter(tipo_unidade='MATRIZ').order_by('created_at').first()

        product = Product.objects.get(id=product_id)

        # Logic for REMOVING stock (Exit, Reversal In, Adjustment Minus)
        if movement_type in ['exit', 'reversal_in', 'adjustment_minus']:
            stocks = ProductStock.objects.filter(
                product=product, 
                distributor=target_distributor, 
                current_stock__gt=0
            ).order_by('expiration_date')
            
            total_available = sum(s.current_stock for s in stocks)
            
            if total_available < quantity:
                messages.error(request, f'Estoque insuficiente. Disponível: {total_available}')
                return redirect('movement_list')

            remaining = quantity
            for stock in stocks:
                if remaining <= 0: break
                
                take = min(stock.current_stock, remaining)
                stock.current_stock -= take
                stock.save()
                remaining -= take
                
                StockMovement.objects.create(
                    product=product,
                    distributor=target_distributor,
                    user=request.user,
                    movement_type=movement_type,
                    quantity=take,
                    previous_stock=stock.current_stock + take,
                    new_stock=stock.current_stock,
                    batch=stock.batch,
                    expiration_date=stock.expiration_date,
                    reason=reason or dict(StockMovementType.choices).get(movement_type, movement_type)
                )
            
            messages.success(request, 'Movimentação realizada com sucesso.')

        # Logic for ADDING stock (Entry, Reversal Out, Adjustment Plus)
        elif movement_type in ['entry', 'reversal_out', 'adjustment_plus']:
            batch = 'S/L'
            if movement_type == 'reversal_out':
                batch = 'ESTORNO'
            elif movement_type == 'entry':
                batch = 'MANUAL'
            
            stock, _ = ProductStock.objects.get_or_create(
                product=product,
                distributor=target_distributor,
                batch=batch,
                defaults={'current_stock': 0}
            )
            
            stock.current_stock += quantity
            stock.save()
            
            StockMovement.objects.create(
                product=product,
                distributor=target_distributor,
                user=request.user,
                movement_type=movement_type,
                quantity=quantity,
                previous_stock=stock.current_stock - quantity,
                new_stock=stock.current_stock,
                batch=batch,
                expiration_date=stock.expiration_date,
                reason=reason or dict(StockMovementType.choices).get(movement_type, movement_type)
            )
            messages.success(request, 'Movimentação realizada com sucesso.')
             
        else:
            messages.error(request, 'Tipo de movimento inválido.')
            return redirect('movement_create')
             
        return redirect('movement_list')

    products = Product.objects.filter(is_active=True)
    distributors = Distributor.objects.filter(is_active=True)
    return render(request, 'stock/movement_form.html', {'products': products, 'distributors': distributors})

@login_required
def get_stock_level(request):
    product_id = request.GET.get('product')
    distributor_id = request.GET.get('distributor')
    
    stock_count = 0
    if product_id and distributor_id:
        try:
            dist = Distributor.objects.get(id=distributor_id)
            if dist.tipo_unidade == 'MATRIZ':
                 master = Distributor.objects.filter(tipo_unidade='MATRIZ').order_by('created_at').first()
                 stock = ProductStock.objects.filter(product_id=product_id, distributor=master).aggregate(total=Sum('current_stock'))['total']
            else:
                 stock = ProductStock.objects.filter(product_id=product_id, distributor_id=distributor_id).aggregate(total=Sum('current_stock'))['total']
            
            stock_count = stock if stock else 0
        except:
            pass
            
    return render(request, 'stock/partials/stock_level.html', {'stock': stock_count})

@login_required
@transaction.atomic
def registrar_entrada(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        distributor_id = request.POST.get('distributor')
        quantity = int(request.POST.get('quantity'))
        batch = request.POST.get('batch')
        expiration_date = request.POST.get('expiration_date')
        
        target_distributor = Distributor.objects.get(id=distributor_id)
        if target_distributor.tipo_unidade == 'MATRIZ':
            target_distributor = Distributor.objects.filter(tipo_unidade='MATRIZ').order_by('created_at').first()
            
        product = Product.objects.get(id=product_id)
        
        stock, _ = ProductStock.objects.get_or_create(
            product=product,
            distributor=target_distributor,
            batch=batch,
            defaults={'current_stock': 0, 'expiration_date': expiration_date}
        )
        
        stock.current_stock += quantity
        stock.save()
        
        StockMovement.objects.create(
            product=product,
            distributor=target_distributor,
            user=request.user,
            movement_type='entry',
            quantity=quantity,
            previous_stock=stock.current_stock - quantity,
            new_stock=stock.current_stock,
            batch=batch,
            expiration_date=expiration_date,
            reason='Entrada Manual'
        )
        messages.success(request, 'Entrada registrada com sucesso.')
        return redirect('movement_list')
        
    products = Product.objects.filter(is_active=True)
    distributors = Distributor.objects.filter(is_active=True)
    return render(request, 'stock/registrar_entrada.html', {'products': products, 'distributors': distributors})

@login_required
@transaction.atomic
def registrar_saida(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        distributor_id = request.POST.get('distributor')
        quantity = int(request.POST.get('quantity'))
        
        target_distributor = Distributor.objects.get(id=distributor_id)
        if target_distributor.tipo_unidade == 'MATRIZ':
            target_distributor = Distributor.objects.filter(tipo_unidade='MATRIZ').order_by('created_at').first()
            
        product = Product.objects.get(id=product_id)
        
        # Simple FIFO-ish or manual batch deduction
        stocks = ProductStock.objects.filter(product=product, distributor=target_distributor, current_stock__gt=0).order_by('expiration_date')
        
        remaining = quantity
        for stock in stocks:
            if remaining <= 0:
                break
            
            take = min(stock.current_stock, remaining)
            stock.current_stock -= take
            stock.save()
            remaining -= take
            
            StockMovement.objects.create(
                product=product,
                distributor=target_distributor,
                user=request.user,
                movement_type='exit',
                quantity=take,
                previous_stock=stock.current_stock + take,
                new_stock=stock.current_stock,
                batch=stock.batch,
                expiration_date=stock.expiration_date,
                reason='Saída Manual'
            )
            
        if remaining > 0 and not request.user.is_superuser:
            messages.warning(request, f'Estoque insuficiente. Faltaram {remaining} itens.')
        else:
            messages.success(request, 'Saída registrada com sucesso.')
            
        return redirect('movement_list')

    products = Product.objects.filter(is_active=True)
    distributors = Distributor.objects.filter(is_active=True)
    return render(request, 'stock/registrar_saida.html', {'products': products, 'distributors': distributors})

@login_required
@transaction.atomic
def ajustar_estoque(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Use helper to determine correct distributor
    distributor = get_stock_distributor(request.user)

    if not distributor:
        if request.user.is_superuser:
            messages.warning(request, 'Superusuário sem distribuidor vinculado. Impossível ajustar estoque automaticamente.')
        else:
            messages.error(request, 'Usuário sem unidade vinculada.')
        return redirect('product_detail', pk=product_id)

    if request.method == 'POST':
        batch = request.POST.get('batch', '').strip()
        expiration_date = request.POST.get('expiration_date')
        quantity_str = request.POST.get('quantity')
        reason_selected = request.POST.get('reason')

        if not batch or not expiration_date or not quantity_str or not reason_selected:
            messages.error(request, 'Todos os campos são obrigatórios.')
            return render(request, 'stock/ajustar_estoque_form.html', {'product': product})

        try:
            new_quantity = int(quantity_str)
            if new_quantity < 0:
                raise ValueError
        except ValueError:
            messages.error(request, 'Quantidade inválida.')
            return render(request, 'stock/ajustar_estoque_form.html', {'product': product})

        # Find or Create Stock
        stock, created = ProductStock.objects.get_or_create(
            product=product,
            distributor=distributor,
            batch=batch,
            defaults={'current_stock': 0, 'expiration_date': expiration_date}
        )
        
        # Update expiration if changed
        if str(stock.expiration_date) != expiration_date:
            stock.expiration_date = expiration_date

        current_stock = stock.current_stock
        diff = new_quantity - current_stock

        if diff == 0:
            stock.save() # Save mainly to update expiration date if changed
            messages.info(request, 'Estoque atualizado (apenas dados do lote). Nenhuma alteração na quantidade.')
            return redirect('product_detail', pk=product_id)

        # Update Stock
        stock.current_stock = new_quantity
        stock.save()

        # Determine Movement Type
        if diff > 0:
            movement_type = 'adjustment_plus'
            move_qty = diff
        else:
            movement_type = 'adjustment_minus'
            move_qty = abs(diff)

        # Create Movement
        StockMovement.objects.create(
            product=product,
            distributor=distributor,
            user=request.user,
            movement_type=movement_type,
            quantity=move_qty,
            previous_stock=current_stock,
            new_stock=new_quantity,
            reason=f"{reason_selected}",
            batch=batch,
            expiration_date=expiration_date
        )

        messages.success(request, f'Estoque ajustado com sucesso! (Anterior: {current_stock} -> Atual: {new_quantity})')
        return redirect('product_detail', pk=product_id)

    return render(request, 'stock/ajustar_estoque_form.html', {'product': product})

@login_required
def dashboard_matriz_consolidado(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso restrito à Matriz.')
        return redirect('product_list')

    # Get all Matriz distributors
    matriz_distributors = Distributor.objects.filter(tipo_unidade='MATRIZ')
    
    stocks = ProductStock.objects.filter(
        product__is_active=True,
        distributor__in=matriz_distributors
    ).select_related('product', 'distributor')
    
    # Structure: {(product_id, batch): {'product': product, 'batch': batch, 'total': 0}}
    data = {}
    
    for stock in stocks:
        key = (stock.product.id, stock.batch)
        if key not in data:
            data[key] = {
                'product': stock.product,
                'batch': stock.batch,
                'total': 0
            }
        
        data[key]['total'] += stock.current_stock
    
    sorted_data = sorted(data.values(), key=lambda x: (x['product'].name, x['batch'] or ''))
    
    return render(request, 'stock/dashboard_consolidado.html', {'report_data': sorted_data})
