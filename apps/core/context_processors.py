from apps.distributors.models import Distributor

def simulator_context(request):
    """
    Disponibiliza dados para a barra de ferramentas de simulação.
    """
    if not request.user.is_authenticated or not request.user.is_superuser:
        return {}
    
    matriz_distributors = Distributor.objects.filter(is_active=True, tipo_unidade='MATRIZ').order_by('name')
    filial_distributors = Distributor.objects.filter(is_active=True, tipo_unidade='FILIAL').order_by('name')

    return {
        'simulator_matriz': matriz_distributors,
        'simulator_filiais': filial_distributors,
        'is_simulating': 'simulated_distributor_id' in request.session,
        'current_simulated_id': request.session.get('simulated_distributor_id')
    }
