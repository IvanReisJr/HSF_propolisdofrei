from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('new/', views.order_create, name='order_create'),
    path('<uuid:pk>/', views.order_detail, name='order_detail'),
    path('<uuid:pk>/confirm/', views.order_confirm, name='order_confirm'),
    path('<uuid:pk>/authorize/', views.order_authorize, name='order_authorize'),
    path('<uuid:pk>/cancel/', views.order_cancel, name='order_cancel'),
    path('<uuid:pk>/delete/', views.order_delete, name='order_delete'),
    
    # Financeiro / Prestação de Contas
    path('financeiro/prestar-contas/<uuid:order_id>/', views.upload_settlement, name='upload_settlement'),
    path('financeiro/meus-pagamentos/', views.settlement_list, name='settlement_list'),
    path('financeiro/pendencias/', views.pending_payments, name='pending_payments'),

    # Auditoria Matriz
    path('matriz/auditoria/', views.audit_list, name='financial_audit_list'),
    path('matriz/auditoria/aprovar/<uuid:pk>/', views.approve_settlement, name='approve_settlement'),
    path('matriz/auditoria/rejeitar/<uuid:pk>/', views.reject_settlement, name='reject_settlement'),
    
    # Relatórios Matriz
    path('matriz/relatorios/fechamento/', views.financial_closure_report, name='financial_closure_report'),
    path('matriz/relatorios/fechamento/pdf/', views.export_closure_pdf, name='export_closure_pdf'),
]
