from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Distributor
from apps.core.constants import BRAZIL_STATES

@login_required
def distributor_list(request):
    distributors = Distributor.objects.filter(is_active=True)
    return render(request, 'distributors/distributor_list.html', {'distributors': distributors})

@login_required
def distributor_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        document = request.POST.get('document', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        notes = request.POST.get('notes', '').strip()
        distributor_type = request.POST.get('distributor_type', 'branch')
        
        # Auto-generate code
        dist_count = Distributor.objects.count()
        next_number = dist_count + 1
        code = f"DIST{next_number:05d}"
        
        form_code = request.POST.get('code', '').strip()
        if form_code:
            code = form_code

        try:
            Distributor.objects.create(
                code=code,
                name=name,
                document=document,
                email=email,
                phone=phone,
                address=address,
                city=city,
                state=state,
                notes=notes,
                distributor_type=distributor_type,
                is_active=True
            )
            messages.success(request, f'Distribuidor "{name}" criado com sucesso no estado {state}!')
            return redirect('distributor_list')
        except Exception as e:
            messages.error(request, f'Erro ao criar distribuidor: {str(e)}')
    
    # Generate next code for display
    dist_count = Distributor.objects.count()
    next_number = dist_count + 1
    next_code = f"DIST{next_number:05d}"
    
    context = {
        'next_code': next_code,
        'states': BRAZIL_STATES
    }
    return render(request, 'distributors/distributor_form.html', context)

@login_required
def distributor_edit(request, pk):
    distributor = get_object_or_404(Distributor, pk=pk)
    
    if request.method == 'POST':
        # Explicit capture
        new_code = request.POST.get('code', '').strip()
        new_name = request.POST.get('name', '').strip()
        new_document = request.POST.get('document', '').strip()
        new_email = request.POST.get('email', '').strip()
        new_phone = request.POST.get('phone', '').strip()
        new_address = request.POST.get('address', '').strip()
        new_city = request.POST.get('city', '').strip()
        new_state = request.POST.get('state', '').strip()
        new_notes = request.POST.get('notes', '').strip()
        new_active = request.POST.get('is_active') == 'on'
        new_type = request.POST.get('distributor_type', 'branch')
        
        if new_code: distributor.code = new_code
        if new_name: distributor.name = new_name
        distributor.document = new_document
        distributor.email = new_email
        distributor.phone = new_phone
        distributor.address = new_address
        distributor.city = new_city
        if new_state: distributor.state = new_state
        distributor.notes = new_notes
        distributor.distributor_type = new_type
        distributor.is_active = new_active
        
        try:
            distributor.save()
            messages.success(request, f'Distribuidor "{distributor.name}" atualizado para {distributor.state}!')
            return redirect('distributor_list')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar: {str(e)}')
    
    context = {
        'distributor': distributor,
        'states': BRAZIL_STATES
    }
    return render(request, 'distributors/distributor_form.html', context)

@login_required
def inativar_distribuidor(request, pk):
    if not request.user.is_super_user_role():
        messages.error(request, 'Apenas administradores podem inativar distribuidores.')
        return redirect('distributor_list')
        
    distributor = get_object_or_404(Distributor, pk=pk)
    
    # Optional: Check if trying to inactivate self (Headquarters often shouldn't update itself this way, but strictly following prompt)
    
    distributor.is_active = False
    distributor.save()
    messages.success(request, 'Distribuidor Inativado!')
    return redirect('distributor_list')
