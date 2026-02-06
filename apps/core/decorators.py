from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect

def matriz_required(view_func):
    """
    Decorator for views that checks if the user belongs to a 'MATRIZ' unit.
    Raises 403 PermissionDenied if not.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        # Superusers are allowed (bypass)
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Check if user has a distributor/unidade
        # Assuming 'unidade' property exists as alias to distributor
        unidade = getattr(request.user, 'unidade', None)
        
        if not unidade:
            # If logic dictates that users MUST have a unit, treat as denied if not superuser
            # Or if logical superuser (is_super_user_role) but is_superuser is false?
            # Let's rely on is_super_user_role if pertinent, but usually is_superuser is safer.
            # Using is_super_user_role() from model:
            if hasattr(request.user, 'is_super_user_role') and request.user.is_super_user_role():
                 return view_func(request, *args, **kwargs)
            raise PermissionDenied("Entidade não associada.")

        # Check tipo_unidade
        # We access the property. Note: The field name in model is 'tipo_unidade'
        if getattr(unidade, 'tipo_unidade', '') != 'MATRIZ':
             raise PermissionDenied("Apenas a Matriz pode realizar esta operação.")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
