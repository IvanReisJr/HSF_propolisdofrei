from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Max
from .models import Product, Packaging, ProductStock
from apps.categories.models import Category
from apps.distributors.models import Distributor
from apps.core.models import UnitOfMeasure
from apps.establishments.models import Establishment

@login_required
def product_list(request):
    products = Product.objects.all().select_related('category', 'unit_fk', 'packaging')
    
    # Isolation: Non-superusers see only their distributor's products
    if not request.user.is_super_user_role():
        products = products.filter(distributor=request.user.distributor)
        
    return render(request, 'products/product_list_v2.html', {'products': products})

@login_required
def product_create(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            category_id = request.POST.get('category')
            unit_id = request.POST.get('unit')
            cost_price = request.POST.get('cost_price')
            sale_price = request.POST.get('sale_price')
            min_stock = request.POST.get('min_stock')
            packaging_id = request.POST.get('packaging')
            status = request.POST.get('status', 'active')
            distributor_id = request.POST.get('distributor')
            
            # Isolation: Force user's distributor if not superuser
            if not request.user.is_super_user_role():
                distributor = request.user.distributor
            else:
                distributor = None
                if distributor_id:
                    distributor = get_object_or_404(Distributor, id=distributor_id)

            # Fetch relational objects
            category = get_object_or_404(Category, id=category_id)
            
            unit_obj = None
            if unit_id:
                unit_obj = get_object_or_404(UnitOfMeasure, id=unit_id)

            packaging = None
            if packaging_id:
                packaging = get_object_or_404(Packaging, id=packaging_id)

            # Robust Code Generation
            # Find the last code used (including deleted ones via all_objects if available, or just rely on manual unique check loop)
            # Product has 'all_objects' manager defined in models.py
            last_prod = Product.all_objects.all().order_by('-code').first()
            next_number = 1
            if last_prod and last_prod.code.startswith('PROD'):
                try:
                    next_number = int(last_prod.code.replace('PROD', '')) + 1
                except ValueError:
                    pass
            
            code = f"PROD{next_number:05d}"
            
            # Conflict Check Loop
            while Product.all_objects.filter(code=code).exists():
                next_number += 1
                code = f"PROD{next_number:05d}"
            
            product = Product(
                name=name,
                code=code,
                category=category,
                unit_fk=unit_obj,
                unit=unit_obj.abbreviation if unit_obj else 'un',
                cost_price=cost_price or 0,
                sale_price=sale_price or 0,
                min_stock=min_stock or 0,
                packaging=packaging,
                status=status,
                distributor=distributor
            )
            product.save()

            # Initialize stock as 0 for all establishments
            for est in Establishment.objects.all():
                ProductStock.objects.get_or_create(product=product, establishment=est, defaults={'current_stock': 0})
                
            messages.success(request, f'Produto {name} criado com sucesso! Código: {code}')
            return redirect('product_list')

        except Exception as e:
            messages.error(request, f'Erro ao criar produto: {e}')
            # Fall through to re-render form with entered data? 
            # ideally we should pass values back to context, but for now simple re-render
            pass 
            
    categories = Category.objects.all()
    units = UnitOfMeasure.objects.all()
    packagings = Packaging.objects.filter(is_active=True)
    try:
        distributors = Distributor.objects.filter(distributor_type='headquarters', is_active=True).order_by('name')
    except Exception:
        distributors = Distributor.objects.filter(is_active=True).order_by('name')
    
    # Generate next code for display (Preview)
    last_prod = Product.all_objects.all().order_by('-code').first()
    next_number = 1
    if last_prod and last_prod.code.startswith('PROD'):
        try:
            next_number = int(last_prod.code.replace('PROD', '')) + 1
        except ValueError:
            pass
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
    # Isolation: Check access
    product = get_object_or_404(Product, pk=pk)
    if not request.user.is_super_user_role() and product.distributor != request.user.distributor:
        messages.error(request, 'Você não tem permissão para editar este produto.')
        return redirect('product_list')
    if request.method == 'POST':
        product.name = request.POST.get('name')
        
        # Only update code if explicitly changed (usually hidden/disabled or manual)
        if request.POST.get('code'):
             product.code = request.POST.get('code')
             
        if request.POST.get('category'):
            product.category_id = request.POST.get('category')
        
        # Handle Unit FK
        unit_id = request.POST.get('unit')
        if unit_id:
            try:
                unit_obj = UnitOfMeasure.objects.get(id=unit_id)
                product.unit_fk = unit_obj
                product.unit = unit_obj.abbreviation
            except (ValueError, UnitOfMeasure.DoesNotExist):
                pass
        
        # Handle Numbers
        product.cost_price = request.POST.get('cost_price')
        product.sale_price = request.POST.get('sale_price')
        product.min_stock = request.POST.get('min_stock')
        product.status = request.POST.get('status') # active/inactive

        # Handle Packaging
        package_id = request.POST.get('packaging')
        if package_id:
            product.packaging_id = package_id
        else:
            product.packaging_id = None
            
        if package_id:
            product.packaging_id = package_id
        else:
            product.packaging_id = None
            
        # Handle Distributor (Only Superusers can change it)
        if request.user.is_super_user_role():
            dist_id = request.POST.get('distributor')
            if dist_id:
                product.distributor_id = dist_id
            else:
                product.distributor_id = None
        # Else: keep existing distributor (enforced by initial fetch)
        
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
        
        try:
            product.save()
            messages.success(request, f'Produto {product.name} atualizado!')
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f'Erro ao salvar: {e}')
            return redirect('product_edit', pk=pk)
        
    categories = Category.objects.all()
    units = UnitOfMeasure.objects.all()
    packagings = Packaging.objects.filter(is_active=True)
    try:
        distributors = Distributor.objects.filter(distributor_type='headquarters', is_active=True).order_by('name')
    except Exception:
        distributors = Distributor.objects.filter(is_active=True).order_by('name')
    
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
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Isolation: Check access
    if not request.user.is_super_user_role() and product.distributor != request.user.distributor:
        messages.error(request, 'Você não tem permissão para inativar este produto.')
        return redirect('product_list')
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Produto inativado com sucesso!')
        return redirect('product_list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Isolation: Check access
    if not request.user.is_super_user_role() and product.distributor != request.user.distributor:
        messages.error(request, 'Você não tem permissão para visualizar este produto.')
        return redirect('product_list')
    # Fetch related checks?
    stock_movements = product.stock_movements.all().order_by('-created_at')[:10]
    stocks = product.stocks.all()
    context = {
        'product': product,
        'stock_movements': stock_movements,
        'stocks': stocks
    }
    return render(request, 'products/product_detail.html', context)

# Packaging Views
@login_required
def packaging_list(request):
    packagings = Packaging.objects.filter(is_active=True)
    return render(request, 'products/packaging_list.html', {'packagings': packagings})

@login_required
def packaging_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Packaging.objects.create(name=name)
            messages.success(request, 'Embalagem criada com sucesso!')
            return redirect('packaging_list')
    return render(request, 'products/packaging_form.html')

@login_required
def packaging_edit(request, pk):
    packaging = get_object_or_404(Packaging, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            packaging.name = name
            packaging.save()
            messages.success(request, 'Embalagem atualizada!')
            return redirect('packaging_list')
    return render(request, 'products/packaging_form.html', {'packaging': packaging})

@login_required
def packaging_delete(request, pk):
    packaging = get_object_or_404(Packaging, pk=pk)
    if request.method == 'POST':
        packaging.delete()
        messages.success(request, 'Embalagem removida!')
        return redirect('packaging_list')
    return render(request, 'products/packaging_confirm_delete.html', {'packaging': packaging})
