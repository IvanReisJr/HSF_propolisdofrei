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

def audit_context(request):
    """
    Disponibiliza contador de aprovações pendentes para Matriz/Admins.
    """
    if not request.user.is_authenticated:
        return {}
        
    # Check if user is Superuser or Matriz
    is_matriz = False
    if request.user.is_superuser:
        is_matriz = True
    elif hasattr(request.user, 'distributor') and request.user.distributor and request.user.distributor.tipo_unidade == 'MATRIZ':
        is_matriz = True
        
    if is_matriz:
        # Import inside function to avoid circular import during startup
        from apps.orders.models import AccountSettlement
        count = AccountSettlement.objects.filter(is_validated=False, rejection_reason__isnull=True).count()
        return {'pending_approvals_count': count}
        
    return {}

def filial_context(request):
    """
    Disponibiliza contador de pendências de pagamento para Filiais.
    """
    if not request.user.is_authenticated:
        return {}
        
    user_distributor = getattr(request.user, 'distributor', None)
    if user_distributor and user_distributor.tipo_unidade == 'FILIAL':
        from apps.orders.models import Order, PaymentCondition, PaymentStatus
        count = Order.objects.filter(
            target_distributor=user_distributor,
            status__in=['confirmado', 'entregue'],
        ).exclude(
            payment_condition=PaymentCondition.DOACAO
        ).exclude(
            payment_status=PaymentStatus.TOTAL
        ).count()
        return {'pending_payments_count': count}
        
    return {}
