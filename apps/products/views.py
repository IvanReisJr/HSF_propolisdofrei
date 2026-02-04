from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, ProductStock, Packaging
from apps.categories.models import Category
from apps.establishments.models import Establishment
from django.db.models import Q

@login_required
def product_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', 'active')
    
    products = Product.objects.all()
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(code__icontains=query)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)
        
    if status and status != 'all':
        products = products.filter(status=status)
        
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'selected_status': status,
    }
    return render(request, 'products/product_list.html', context)

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # Get stock for all establishments for this product
    stocks = ProductStock.objects.filter(product=product)
    
    context = {
        'product': product,
        'stocks': stocks,
    }
    return render(request, 'products/product_detail.html', context)

@login_required
def product_create(request):
    if request.method == 'POST':
        # Simple manual form handling for now, can use ModelForm later
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        unit = request.POST.get('unit')
        cost_price = request.POST.get('cost_price')
        sale_price = request.POST.get('sale_price')
        min_stock = request.POST.get('min_stock')
        packaging_id = request.POST.get('packaging')
        status = request.POST.get('status', 'active')
        distributor_id = request.POST.get('distributor')
        
        category = get_object_or_404(Category, id=category_id)
        
        # Auto-generate code based on total count
        product_count = Product.objects.count()
        next_number = product_count + 1
        code = f"PROD{next_number:05d}"
        
        product = Product.objects.create(
            name=name,
            code=code,
            category=category,
            unit=unit, # Will be ID if from dropdown, need to fix?
            cost_price=cost_price,
            sale_price=sale_price,
            min_stock=min_stock,
            packaging_id=packaging_id,
            status=status,
            distributor_id=distributor_id if distributor_id else None
        )
        
        # Handle Unit FK
        if unit:
            try:
                from apps.core.models import UnitOfMeasure
                unit_obj = UnitOfMeasure.objects.get(id=unit)
                product.unit_fk = unit_obj
                product.unit = unit_obj.abbreviation
                product.save()
            except:
                pass
        
        # Initialize stock as 0 for all establishments
        for est in Establishment.objects.all():
            ProductStock.objects.get_or_create(product=product, establishment=est, defaults={'current_stock': 0})
            
        messages.success(request, f'Produto {name} criado com sucesso!')
        return redirect('product_list')
        
    categories = Category.objects.all()
    from apps.core.models import UnitOfMeasure
    units = UnitOfMeasure.objects.all()
    packagings = Packaging.objects.filter(is_active=True)
    
    # Get only Matriz (headquarters) distributors
    from apps.distributors.models import Distributor
    distributors = Distributor.objects.filter(distributor_type='headquarters', is_active=True).order_by('name')
    
    # Generate next code for display
    product_count = Product.objects.count()
    next_number = product_count + 1
    next_code = f"PROD{next_number:05d}"
    
    context = {
        'categories': categories,
        'units': units,
        'packagings': packagings,
        'distributors': distributors,
        'next_code': next_code
    }
    return render(request, 'products/product_form.html', context)

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.code = request.POST.get('code')
        product.category_id = request.POST.get('category')
        
        # Handle Unit FK
        unit_id = request.POST.get('unit')
        if unit_id:
            try:
                # If it's a UUID, use it directly (from new dropdown)
                product.unit_fk_id = unit_id
                # Update char field for compatibility
                product.unit = product.unit_fk.abbreviation
            except:
                # Fallback if text passed (legacy)
                product.unit = unit_id
                
        product.cost_price = request.POST.get('cost_price')
        product.sale_price = request.POST.get('sale_price')
        product.min_stock = request.POST.get('min_stock')
        product.status = request.POST.get('status')

        product.packaging_id = request.POST.get('packaging')
        product.distributor_id = request.POST.get('distributor') or None
        
        # Validations
        try:
            cost = float(product.cost_price or 0)
            sale = float(product.sale_price or 0)
            min_stk = int(product.min_stock or 0)
            
            if cost >= sale:
                messages.error(request, 'Preço de custo deve ser menor que preço de venda!')
                return redirect('product_edit', pk=pk)
            
            if min_stk <= 0:
                messages.error(request, 'Estoque mínimo deve ser maior que zero!')
                return redirect('product_edit', pk=pk)
        except ValueError:
            messages.error(request, 'Valores inválidos nos campos numéricos!')
            return redirect('product_edit', pk=pk)
        
        product.save()
        
        messages.success(request, f'Produto {product.name} atualizado!')
        return redirect('product_list')
        
    categories = Category.objects.all()
    from apps.core.models import UnitOfMeasure
    units = UnitOfMeasure.objects.all()
    packagings = Packaging.objects.filter(is_active=True)
    
    # Get only Matriz (headquarters) distributors
    from apps.distributors.models import Distributor
    distributors = Distributor.objects.filter(distributor_type='headquarters', is_active=True).order_by('name')
    
    context = {
        'product': product,
        'categories': categories,
        'units': units,
        'packagings': packagings,
        'distributors': distributors,
        'is_edit': True
    }
    return render(request, 'products/product_form.html', context)

@login_required
def packaging_list(request):
    packagings = Packaging.objects.all().order_by('name')
    context = {
        'packagings': packagings
    }
    return render(request, 'products/packaging_list.html', context)

@login_required
def packaging_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        is_active = request.POST.get('is_active') == 'on'
        
        if name:
            Packaging.objects.create(name=name, is_active=is_active)
            messages.success(request, f'Embalagem "{name}" criada com sucesso!')
            return redirect('packaging_list')
        else:
            messages.error(request, 'Nome é obrigatório.')
            
    return render(request, 'products/packaging_form.html')

@login_required
def packaging_edit(request, pk):
    packaging = get_object_or_404(Packaging, pk=pk)
    
    if request.method == 'POST':
        packaging.name = request.POST.get('name')
        packaging.is_active = request.POST.get('is_active') == 'on'
        packaging.save()
        messages.success(request, f'Embalagem "{packaging.name}" atualizada!')
        return redirect('packaging_list')
        
    context = {
        'packaging': packaging,
        'is_edit': True
    }
    return render(request, 'products/packaging_form.html', context)

@login_required
def product_delete(request, pk):
    """Soft delete - inativa o produto ao invés de deletar"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.status = 'inactive'
        product.save()
        messages.success(request, f'Produto "{product.name}" inativado com sucesso!')
        return redirect('product_list')
    
    context = {
        'product': product
    }
    return render(request, 'products/product_confirm_delete.html', context)
