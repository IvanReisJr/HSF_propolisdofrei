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
        movements = StockMovement.objects.filter(product__distributor=user.distributor).order_by('-created_at')
    
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
    if not request.user.is_super_user_role():
        products = products.filter(distributor=request.user.distributor)
    establishments = Establishment.objects.all()
        
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

from django.db import transaction

@login_required
@transaction.atomic
def registrar_entrada(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity'))
        batch = request.POST.get('batch', 'S/L').strip() or 'S/L'
        expiration_date = request.POST.get('expiration_date') or None # Default None if empty string
        
        # Security: Get Product (and implicitly check isolation in GET, but double check here?)
        product = get_object_or_404(Product, id=product_id)
        
        # Logic: Unidade = request.user.distributor
        distributor = request.user.distributor
        
        if not distributor and not request.user.is_superuser:
            messages.error(request, 'Usuário sem unidade vinculada.')
            return redirect('registrar_entrada')

        # Logic: Get/Create Stock by Batch
        # Note: defaults only used if created. If exists, we just update stock.
        # Expiration date is usually fixed per batch.
        stock, created = ProductStock.objects.get_or_create(
            product=product, 
            distributor=distributor, 
            batch=batch,
            defaults={'current_stock': 0, 'expiration_date': expiration_date}
        )
        
        if created and expiration_date:
            stock.expiration_date = expiration_date

        stock.current_stock += quantity
        stock.save()
        
        # Logic: Create Movement
        StockMovement.objects.create(
            product=product,
            distributor=distributor,
            user=request.user,
            movement_type='entry',
            quantity=quantity,
            previous_stock=stock.current_stock - quantity,
            new_stock=stock.current_stock,
            reason="Entrada Manual",
            batch=batch,
            expiration_date=expiration_date
        )
        
        messages.success(request, f'Entrada de {quantity} {product.unit} (Lote: {batch}) registrada com sucesso!')
        return redirect('registrar_entrada')

    # GET: Active Products only
    products = Product.objects.filter(is_active=True)
    if not request.user.is_super_user_role():
        products = products.filter(distributor=request.user.distributor)
        
    return render(request, 'stock/registrar_entrada.html', {'products': products})

from django.db.models import Sum

@login_required
def dashboard_matriz_consolidado(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso restrito à Matriz.')
        return redirect('product_list')

    # Aggregating stock by Distributor and Product
    # Using 'distributor__name' and 'product__name' grouping
    stock_data = ProductStock.objects.filter(product__is_active=True)\
        .values('distributor__name', 'product__name', 'product__min_stock')\
        .annotate(total=Sum('current_stock'))\
        .order_by('distributor__name', 'product__name')
        
    return render(request, 'stock/dashboard_consolidado.html', {'stock_data': stock_data})

@login_required
@transaction.atomic
def registrar_saida(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity'))
        batch = request.POST.get('batch') # Now required to select from which batch
        reason = request.POST.get('reason', 'Saída Manual')
        
        # Security: Get Product
        product = get_object_or_404(Product, id=product_id)
        
        # Logic: Unidade = request.user.distributor
        distributor = request.user.distributor
        
        if not distributor and not request.user.is_superuser:
            messages.error(request, 'Usuário sem unidade vinculada.')
            return redirect('registrar_saida')

        if not batch:
             messages.error(request, 'Selecione o Lote do produto.')
             return redirect('registrar_saida')
             
        # Logic: Get Stock by Batch (Must exist for exit)
        stock = ProductStock.objects.filter(
            product=product,
            distributor=distributor,
            batch=batch
        ).first()
        
        if not stock:
            messages.error(request, f'Lote {batch} não encontrado no estoque desta unidade.')
            return redirect('registrar_saida')
            
        # VALIDAÇÃO DE SALDO (Stock Validation)
        if stock.current_stock < quantity:
            messages.error(request, f'Saldo insuficiente no Lote {batch}! Disp: {stock.current_stock}')
            return redirect('registrar_saida')
        
        # Update Stock
        stock.current_stock -= quantity
        stock.save()
        
        # Logic: Create Movement
        StockMovement.objects.create(
            product=product,
            distributor=distributor,
            user=request.user,
            movement_type='exit',
            quantity=quantity,
            previous_stock=stock.current_stock + quantity,
            new_stock=stock.current_stock,
            reason=reason,
            batch=batch,
            expiration_date=stock.expiration_date
        )
        
        messages.success(request, f'Saída de {quantity} {product.unit} do Lote {batch} registrada com sucesso!')
        return redirect('registrar_saida')

    # GET: Active Products only (and preferably those with stock > 0, but listing all active is fine)
    products = Product.objects.filter(is_active=True)
    if not request.user.is_super_user_role():
        products = products.filter(distributor=request.user.distributor)
        
    return render(request, 'stock/registrar_saida.html', {'products': products})
