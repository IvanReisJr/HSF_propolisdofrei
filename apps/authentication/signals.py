from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth import logout
from django.contrib import messages
from django.core.exceptions import PermissionDenied

@receiver(user_logged_in)
def check_distributor_status(sender, user, request, **kwargs):
    """
    Verifica se o distribuidor do usuário está ativo após o login.
    Se estiver inativo, desconecta o usuário imediatamente.
    """
    # Superusuários (Staff/Admin) não são bloqueados por inativação de distribuidor
    # (Ou dependendo da regra, talvez devam ser se estiverem vinculados, mas geralmente Admin acessa tudo)
    if user.is_superuser or user.is_staff:
        return

    if user.distributor and not user.distributor.is_active:
        # Distribuidor inativado -> Logout forçado
        logout(request)
        messages.error(request, 'Acesso Negado: Sua unidade/distribuidor está inativa. Contate a Matriz.')
        # Opcional: Levantar exceção para interromper o fluxo se necessário, 
        # mas logout + redirect (que o login view faz) é mais suave.
        # Porém, user_logged_in acontece DEPOIS da sessão criada.
        # PermissionDenied levará a uma página de erro 403.
        raise PermissionDenied('Unidade Inativa')
