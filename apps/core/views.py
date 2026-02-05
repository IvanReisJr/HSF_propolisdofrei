from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UnitOfMeasure

@login_required
def unit_list(request):
    units = UnitOfMeasure.objects.filter(is_active=True)
    return render(request, 'core/unit_list.html', {'units': units})

@login_required
def unit_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        abbreviation = request.POST.get('abbreviation')
        
        try:
            UnitOfMeasure.objects.create(name=name, abbreviation=abbreviation, is_active=True)
            messages.success(request, 'Unidade criada com sucesso!')
            return redirect('unit_list')
        except Exception as e:
            messages.error(request, 'Erro ao criar unidade. Verifique se o nome ou sigla já existem.')
    
    return render(request, 'core/unit_form.html')

@login_required
def unit_edit(request, pk):
    unit = get_object_or_404(UnitOfMeasure, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        abbreviation = request.POST.get('abbreviation')
        
        # Simple manual update (could use forms.py for better validation)
        unit.name = name
        unit.abbreviation = abbreviation
        try:
            unit.save()
            messages.success(request, 'Unidade atualizada com sucesso!')
            return redirect('unit_list')
        except Exception as e:
            messages.error(request, 'Erro ao atualizar. Sigla ou nome duplicado.')
    
    return render(request, 'core/unit_form.html', {'unit': unit})

@login_required
def inativar_unidade(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Apenas a equipe da Matriz pode inativar unidades.')
        return redirect('unit_list')

    unit = get_object_or_404(UnitOfMeasure, pk=pk)
    unit.is_active = False
    unit.save()
    messages.success(request, 'Unidade inativada com sucesso!')
    return redirect('unit_list')
