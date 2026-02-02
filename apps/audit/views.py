from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import AuditLog

@login_required
def audit_list(request):
    # Only staff can see audit logs usually
    if not request.user.is_staff:
        return render(request, '403.html', status=403)
        
    logs = AuditLog.objects.all().order_by('-occurred_at')
    
    # Simple filters
    user_q = request.GET.get('user')
    action = request.GET.get('action')
    resource = request.GET.get('resource')
    
    if user_q:
        logs = logs.filter(user__username__icontains=user_q)
    if action:
        logs = logs.filter(action=action)
    if resource:
        logs = logs.filter(resource_type__icontains=resource)
        
    context = {
        'logs': logs[:100], # Limit to last 100 for performance
        'actions': AuditLog.objects.values_list('action', flat=True).distinct(),
    }
    return render(request, 'audit/audit_list.html', context)
