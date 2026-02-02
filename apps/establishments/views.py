from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Establishment
from apps.core.constants import BRAZIL_STATES

@login_required
def establishment_list(request):
    establishments = Establishment.objects.all()
    context = {'establishments': establishments}
    return render(request, 'establishments/establishment_list.html', context)

@login_required
def establishment_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        
        # Auto-generate code
        est_count = Establishment.objects.count()
        next_number = est_count + 1
        code = f"UNIT{next_number:03d}"
        
        form_code = request.POST.get('code', '').strip()
        if form_code:
            code = form_code
            
        try:
            Establishment.objects.create(
                code=code, name=name, city=city, state=state, 
                address=address, phone=phone, email=email
            )
            messages.success(request, f'Unidade {name} criada com sucesso no estado {state}!')
            return redirect('establishment_list')
        except Exception as e:
            messages.error(request, f'Erro ao criar unidade: {str(e)}')
        
    # Generate next code for display
    est_count = Establishment.objects.count()
    next_number = est_count + 1
    next_code = f"UNIT{next_number:03d}"
    
    context = {
        'next_code': next_code,
        'states': BRAZIL_STATES
    }
    return render(request, 'establishments/establishment_form.html', context)

@login_required
def establishment_edit(request, pk):
    establishment = get_object_or_404(Establishment, pk=pk)
    if request.method == 'POST':
        # Explicitly capture each field
        new_code = request.POST.get('code', '').strip()
        new_name = request.POST.get('name', '').strip()
        new_city = request.POST.get('city', '').strip()
        new_state = request.POST.get('state', '').strip()
        new_address = request.POST.get('address', '').strip()
        new_phone = request.POST.get('phone', '').strip()
        new_email = request.POST.get('email', '').strip()
        new_active = request.POST.get('is_active') == 'on'

        # Update object
        if new_code: establishment.code = new_code
        if new_name: establishment.name = new_name
        if new_city: establishment.city = new_city
        if new_state: establishment.state = new_state
        
        establishment.address = new_address
        establishment.phone = new_phone
        establishment.email = new_email
        establishment.is_active = new_active
        
        try:
            establishment.save()
            messages.success(request, f'Unidade "{establishment.name}" atualizada com sucesso para {establishment.state}!')
            return redirect('establishment_list')
        except Exception as e:
            messages.error(request, f'Erro ao salvar: {str(e)}')
        
    context = {
        'establishment': establishment, 
        'is_edit': True,
        'states': BRAZIL_STATES
    }
    return render(request, 'establishments/establishment_form.html', context)
