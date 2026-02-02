from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, ProductStock
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
        
        category = get_object_or_404(Category, id=category_id)
        
        # Auto-generate code based on total count
        product_count = Product.objects.count()
        next_number = product_count + 1
        code = f"PROD{next_number:05d}"
        
        product = Product.objects.create(
            name=name,
            code=code,
            category=category,
            unit=unit,
            cost_price=cost_price,
            sale_price=sale_price,
            min_stock=min_stock
        )
        
        # Initialize stock as 0 for all establishments
        for est in Establishment.objects.all():
            ProductStock.objects.get_or_create(product=product, establishment=est, defaults={'current_stock': 0})
            
        messages.success(request, f'Produto {name} criado com sucesso!')
        return redirect('product_list')
        
    categories = Category.objects.all()
    # Generate next code for display
    product_count = Product.objects.count()
    next_number = product_count + 1
    next_code = f"PROD{next_number:05d}"
    
    context = {
        'categories': categories,
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
        product.unit = request.POST.get('unit')
        product.cost_price = request.POST.get('cost_price')
        product.sale_price = request.POST.get('sale_price')
        product.min_stock = request.POST.get('min_stock')
        product.status = request.POST.get('status')
        product.save()
        
        messages.success(request, f'Produto {product.name} atualizado!')
        return redirect('product_list')
        
    categories = Category.objects.all()
    context = {
        'product': product,
        'categories': categories,
        'is_edit': True
    }
    return render(request, 'products/product_form.html', context)
