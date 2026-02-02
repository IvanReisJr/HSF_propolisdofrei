from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category

@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'categories/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        Category.objects.create(name=name, description=description)
        messages.success(request, 'Categoria criada com sucesso!')
        return redirect('category_list')
    
    return render(request, 'categories/category_form.html')

@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        category.save()
        
        messages.success(request, 'Categoria atualizada com sucesso!')
        return redirect('category_list')
    
    return render(request, 'categories/category_form.html', {'category': category})
