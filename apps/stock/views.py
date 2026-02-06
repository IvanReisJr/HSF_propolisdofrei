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
        distributor_id = request.POST.get('distributor')
        quantity = int(request.POST.get('quantity'))
        batch = request.POST.get('batch', '').strip()
        expiration_date = request.POST.get('expiration_date') or None 
        
        # Validations
        if not batch:
            messages.error(request, 'O campo Lote é obrigatório.')
            return redirect('registrar_entrada')
            
        if not expiration_date:
            messages.error(request, 'O campo Data de Validade é obrigatório.')
            return redirect('registrar_entrada')
            
        # Validation: Stock integrity (No expired products)
        from django.utils import timezone
        import datetime
        
        # Convert string to date if needed (though Django forms usually handle this, raw POST needs parsing)
        if isinstance(expiration_date, str):
            exp_date_obj = datetime.datetime.strptime(expiration_date, '%Y-%m-%d').date()
        else:
            exp_date_obj = expiration_date
            
        if exp_date_obj < timezone.now().date():
            messages.error(request, 'Não é permitida a entrada de produtos vencidos.')
            return redirect('registrar_entrada')

        product = get_object_or_404(Product, id=product_id)
        
        # Validate Distributor (must be a Matriz)
        from apps.distributors.models import Distributor
        distributor = get_object_or_404(Distributor, id=distributor_id)
        
        # Check if it is a Matriz (using both new and old fields for safety)
        if distributor.tipo_unidade != 'MATRIZ' and distributor.distributor_type != 'headquarters':
             messages.error(request, 'O destino deve ser uma Matriz (CD).')
             return redirect('registrar_entrada')

        # Logic: Get/Create Stock by Batch
        # If exists, we sum quantity. If not, we create.
        stock, created = ProductStock.objects.get_or_create(
            product=product, 
            distributor=distributor, 
            batch=batch,
            defaults={'current_stock': 0, 'expiration_date': expiration_date}
        )
        
        # Check consistency of expiration date for existing batch
        if not created and str(stock.expiration_date) != expiration_date:
             messages.warning(request, f'Atenção: A data de validade deste lote foi atualizada de {stock.expiration_date} para {expiration_date}.')
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
            reason="Entrada Manual de Mercadoria",
            batch=batch,
            expiration_date=expiration_date
        )
        
        messages.success(request, f'Entrada de {quantity} {product.unit} (Lote: {batch}) registrada com sucesso para {distributor.name}!')
        return redirect('registrar_entrada')

    # GET
    from apps.distributors.models import Distributor
    from django.db.models import Q
    
    products = Product.objects.filter(is_active=True).order_by('name')
    
    # Filter only Matrizes (CDs)
    matrizes = Distributor.objects.filter(
        Q(tipo_unidade='MATRIZ') | Q(distributor_type='headquarters')
    ).filter(is_active=True).order_by('name')
        
    return render(request, 'stock/registrar_entrada.html', {
        'products': products,
        'distributors': matrizes
    })

from django.db.models import Sum

@login_required
def dashboard_matriz_consolidado(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso restrito à Matriz.')
        return redirect('product_list')

    stocks = ProductStock.objects.filter(product__is_active=True).select_related('product', 'distributor')
    
    # Structure: {(product_id, batch): {'product': product, 'batch': batch, 'humanitas': 0, 'sede_adm': 0, 'total': 0}}
    data = {}
    
    for stock in stocks:
        key = (stock.product.id, stock.batch)
        if key not in data:
            data[key] = {
                'product': stock.product,
                'batch': stock.batch,
                'humanitas': 0,
                'sede_adm': 0,
                'total': 0
            }
        
        # Check distributor name
        dist_name = stock.distributor.name.lower().strip() if stock.distributor else ""
        
        if 'humanitas' in dist_name:
            data[key]['humanitas'] += stock.current_stock
        elif 'sede adm' in dist_name:
            data[key]['sede_adm'] += stock.current_stock
            
        # Total Global includes all distributors
        data[key]['total'] += stock.current_stock
        
    # Sort by product name then batch
    sorted_data = sorted(data.values(), key=lambda x: (x['product'].name, x['batch'] or ''))
        
    return render(request, 'stock/dashboard_consolidado.html', {'report_data': sorted_data})

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
