from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.decorators import matriz_required
from .models import Category

@login_required
@matriz_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'categories/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = 'is_active' in request.POST
        
        try:
            Category.objects.create(name=name, description=description, is_active=is_active)
            messages.success(request, 'Categoria criada com sucesso!')
            return redirect('category_list')
        except Exception as e:
            messages.error(request, f'Erro ao criar categoria: {e}')
            # Fallthrough to render form with data could be better, but staying consistent with simple style
    
    return render(request, 'categories/category_form.html')

@login_required
@matriz_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        try:
            category.name = request.POST.get('name')
            category.description = request.POST.get('description')
            category.is_active = 'is_active' in request.POST
            category.save()
            
            messages.success(request, 'Categoria atualizada com sucesso!')
            return redirect('category_list')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar categoria: {e}')
    
    return render(request, 'categories/category_form.html', {'category': category})

@login_required
@matriz_required
def inativar_categoria(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.is_active = False
    category.save()
    messages.success(request, 'Categoria inativada com sucesso!')
    return redirect('category_list')
