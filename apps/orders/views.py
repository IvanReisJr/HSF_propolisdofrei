from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from .models import Order, OrderItem, AccountSettlement, PaymentStatus, PaymentCondition, OrderStatus
from .forms import SettlementUploadForm
from apps.products.models import Product, ProductStock
from apps.distributors.models import Distributor
from apps.stock.models import StockMovement
from django.db import transaction
import traceback
import logging

logger = logging.getLogger(__name__)

@login_required
def order_list(request):
    user = request.user
    status_filter = request.GET.get('status', 'all')
    
    if user.is_super_user_role():
        orders = Order.objects.all()
    else:
        # Filter by Target Distributor (The Filial)
        if hasattr(request.user, 'distributor') and request.user.distributor:
            orders = Order.objects.filter(target_distributor=request.user.distributor)
        else:
            orders = Order.objects.none()
    
    # Apply status filter
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    orders = orders.order_by('-created_at')
    
    context = {
        'orders': orders,
        'status_filter': status_filter
    }
    return render(request, 'orders/order_list.html', context)

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    context = {'order': order}
    return render(request, 'orders/order_detail.html', context)

@login_required
def order_create(request):
    if request.method == 'POST':
        distributor_id = request.POST.get('distributor')
        payment_condition = request.POST.get('payment_condition', PaymentCondition.VISTA)
        
        product_ids = request.POST.getlist('products[]')
        quantities = request.POST.getlist('quantities[]')
        unit_prices = request.POST.getlist('unit_prices[]')
        
        if not product_ids:
            messages.error(request, 'Adicione pelo menos um produto ao pedido.')
            return redirect('order_create')

        try:
            with transaction.atomic():
                # Isolation: Use user's distributor AS TARGET (Requester)
                target_distributor = getattr(request.user, 'distributor', None)
                
                # Source Distributor (Supplying CD) comes from Form
                if not distributor_id:
                    raise Exception("Selecione o Centro de Distribuição (Matriz).")
                
                source_distributor = get_object_or_404(Distributor, id=distributor_id)
                
                # Validation: Cannot order from self if self is Matriz? Or just allow?
                # Prompt says: "Garanta que uma Filial não consiga 'escolher' outra Filial como origem"
                # Filter in context ensures only MATRIZ are shown, but backend check is good.
                if getattr(source_distributor, 'tipo_unidade', '') != 'MATRIZ':
                    raise Exception("A origem deve ser uma MATRIZ.")

                order = Order.objects.create(
                    distributor=source_distributor,    # Source
                    target_distributor=target_distributor, # Target
                    user=request.user,
                    status='pendente',
                    payment_condition=payment_condition,
                    total_amount=0
                )
                
                total = 0
                for pid, qty, u_price in zip(product_ids, quantities, unit_prices):
                    if not qty or int(qty) <= 0: continue
                    
                    product = get_object_or_404(Product, id=pid)
                    
                    # SECURITY: Block inactive products
                    if not product.is_active:
                        raise Exception(f'Produto {product.name} está inativo e não pode ser incluído.')

                    qty = int(qty)
                    
                    try:
                        clean_price = u_price.replace('.', '').replace(',', '.')
                        price = float(clean_price)
                    except ValueError:
                        price = product.sale_price
                        
                    subtotal = price * qty
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        unit_price=price,
                        total_price=subtotal
                    )
                    total += subtotal
                
                order.total_amount = total
                order.save()
                
                messages.success(request, f'Pedido {order.order_number} criado!')
                return redirect('order_detail', pk=order.pk)
        except Exception as e:
            messages.error(request, f'Erro ao criar pedido: {str(e)}')
            return redirect('order_create')
            
    # Distributors: Show ONLY MATRIZ options for source selection
    distributors = Distributor.objects.filter(tipo_unidade='MATRIZ', is_active=True)
    # SECURITY: Filter only active products
    products = Product.objects.filter(is_active=True)
    if request.user.distributor:
         # Show all active products available (Global catalog or restricted?)
         # Usually Filial can order any active product from Matriz.
         # So we list all active products.
         pass

    context = {
        'distributors': distributors,
        'products': products,
        'target_distributor': request.user.distributor,
        'payment_conditions': PaymentCondition.choices,
    }
    return render(request, 'orders/order_form.html', context)

@login_required
def order_authorize(request, pk):
    """
    Permite que a Matriz autorize um pedido pendente.
    """
    order = get_object_or_404(Order, pk=pk)
    
    # Verifica permissão: Apenas Matriz pode autorizar
    user_distributor = getattr(request.user, 'distributor', None)
    if not user_distributor or user_distributor.tipo_unidade != 'MATRIZ':
        if not request.user.is_super_user_role():
            messages.error(request, 'Apenas a Matriz pode autorizar pedidos.')
            return redirect('order_detail', pk=pk)

    if order.status != 'pendente':
        messages.error(request, 'Apenas pedidos pendentes podem ser autorizados.')
        return redirect('order_detail', pk=pk)
    
    order.status = 'autorizado'
    order.save()
    messages.success(request, f'Pedido {order.order_number} autorizado! Aguardando confirmação de recebimento pela Filial.')
    return redirect('order_detail', pk=pk)

@login_required
def order_confirm(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    # Verifica se o pedido está autorizado
    if order.status != 'autorizado':
        messages.error(request, 'Este pedido precisa ser autorizado pela Matriz antes de ser confirmado.')
        return redirect('order_detail', pk=pk)
        
    try:
        with transaction.atomic():
            for item in order.items.all():
                quantity_to_deduct = item.quantity
                product = item.product
                
                # Determine Distributor (Context of Stock Out)
                # If Order has a distributor, use it. Else fallback to user's?
                # Assuming Order.distributor is the SOURCE of the goods (Seller) or TARGET?
                # Usually Order.distributor is the entity PLACING the order in this model?
                # IF this is a Sales Order, we deduct from established source.
                # FOR SIMULATION: We assume we are deducting from the Order's associated Distributor.
                distributor = order.distributor 
                if not distributor:
                     raise Exception("Pedido sem Distribuidor vinculado. Não é possível baixar estoque.")

                # FIFO Strategy: Operations on (Distributor + Product), ordered by Expiry
                # SOURCE DISTRIBUTOR (Quem entrega) perde estoque
                # TARGET DISTRIBUTOR (Quem pediu) recebe estoque?
                # Regra de negócio: Se for TRANSFERÊNCIA, sai da Origem e entra no Destino.
                # Se for VENDA FINAL, sai da Origem e some.
                
                # Neste contexto (Filial pedindo p/ Matriz), a Matriz perde estoque e a Filial ganha.
                # 1. Baixa na Origem (Matriz)
                source_distributor = order.distributor 
                
                if not source_distributor:
                     raise Exception("Pedido sem Distribuidor de Origem vinculado.")

                # POOL DE ESTOQUE: Se a origem for MATRIZ, busca em TODAS as MATRIZes.
                # CD Humanitas e CD Sede Adm compartilham o mesmo estoque físico.
                if source_distributor.tipo_unidade == 'MATRIZ':
                    all_matriz = Distributor.objects.filter(tipo_unidade='MATRIZ', is_active=True)
                    stocks = ProductStock.objects.filter(
                        product=product,
                        distributor__in=all_matriz,
                        current_stock__gt=0
                    ).order_by('expiration_date', 'updated_at')
                else:
                    stocks = ProductStock.objects.filter(
                        product=product,
                        distributor=source_distributor,
                        current_stock__gt=0
                    ).order_by('expiration_date', 'updated_at')
                
                total_available = sum(s.current_stock for s in stocks)
                
                if total_available < quantity_to_deduct:
                    raise Exception(f'Estoque insuficiente na Origem ({source_distributor.name}) para {product.name}. Disponível: {total_available}')
                
                deducted_total = 0
                for stock in stocks:
                    if quantity_to_deduct <= 0:
                        break
                        
                    deduct = min(stock.current_stock, quantity_to_deduct)
                    previous_stock = stock.current_stock
                    stock.current_stock -= deduct
                    stock.save()
                    
                    quantity_to_deduct -= deduct
                    deducted_total += deduct
                    
                    # Record movement (SAÍDA da Origem)
                    StockMovement.objects.create(
                        product=product,
                        distributor=source_distributor,
                        user=request.user,
                        movement_type='exit',
                        quantity=deduct,
                        reason=f'Pedido {order.order_number} confirmado - Envio para {order.target_distributor.name}',
                        batch=stock.batch,
                        expiration_date=stock.expiration_date,
                        previous_stock=previous_stock,
                        new_stock=stock.current_stock,
                        reference_id=order.id,
                        reference_type='order'
                    )
                
                # 2. Entrada no Destino (Filial)
                target_distributor = order.target_distributor
                if target_distributor:
                    # Verifica se já existe estoque desse produto/lote no destino, ou cria novo
                    # Simplificação: Cria um novo registro ou soma no existente (LIFO/FIFO mixing risk?)
                    # Vamos somar no lote mais novo ou criar um genérico se não tiver info de lote da origem transferida
                    # Idealmente, transferimos o lote exato.
                    
                    # Como iteramos sobre múltiplos lotes na origem, precisamos replicar essa estrutura no destino?
                    # Para simplificar agora: Adicionamos o total deduzido em um registro "Consolidado" ou no primeiro lote encontrado?
                    # Correto: Iterar e transferir lote a lote. Mas aqui simplificamos somando ao lote 'S/L' ou criando.
                    
                    # Melhor abordagem: Entrar como 'Transferência de Entrada'
                    target_stock, created = ProductStock.objects.get_or_create(
                        product=product,
                        distributor=target_distributor,
                        batch='TRANSF-' + str(order.order_number), # Identifica origem
                        defaults={
                            'current_stock': 0,
                            'expiration_date': None # Deveria vir do lote origem
                        }
                    )
                    
                    previous_target_stock = target_stock.current_stock
                    target_stock.current_stock += deducted_total
                    target_stock.save()
                    
                    StockMovement.objects.create(
                        product=product,
                        distributor=target_distributor,
                        user=request.user,
                        movement_type='entry',
                        quantity=deducted_total,
                        reason=f'Recebimento Pedido {order.order_number} de {source_distributor.name}',
                        batch=target_stock.batch,
                        previous_stock=previous_target_stock,
                        new_stock=target_stock.current_stock,
                        reference_id=order.id,
                        reference_type='order'
                    )
            
            order.status = 'confirmado'
            order.save()
            messages.success(request, f'Pedido {order.order_number} recebido e estoque atualizado com sucesso!')
    except Exception as e:
        messages.error(request, str(e))
        
    return redirect('order_detail', pk=pk)

@login_required
def order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status != 'pendente':
        messages.error(request, 'Apenas pedidos pendentes podem ser cancelados.')
    else:
        order.status = 'cancelado'
        order.save()
        messages.success(request, 'Pedido cancelado.')
    return redirect('order_detail', pk=pk)

@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    # Restrict deletion to pending or canceled orders
    if order.status not in ['pendente', 'cancelado']:
        messages.error(request, 'Apenas pedidos pendentes ou cancelados podem ser excluídos.')
        return redirect('order_detail', pk=pk)
        
    if request.method == 'POST':
        order_number = order.order_number
        order.delete()
        messages.success(request, f'Pedido {order_number} excluído com sucesso.')
        return redirect('order_list')
        
    context = {'order': order}
    return render(request, 'orders/order_confirm_delete.html', context)

@login_required
def upload_settlement(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Security: Ensure user belongs to the same distributor as the order (Target)
    if not request.user.is_super_user_role():
        user_distributor = getattr(request.user, 'distributor', None)
        if not user_distributor or order.target_distributor != user_distributor:
             messages.error(request, "Você não tem permissão para prestar contas deste pedido.")
             return redirect('order_list')

    if request.method == 'POST':
        form = SettlementUploadForm(request.POST, request.FILES, order=order)
        if form.is_valid():
            settlement = form.save(commit=False)
            settlement.order = order
            settlement.save()
            
            # Update Order payment status
            order.payment_status = PaymentStatus.PENDENTE
            order.save()
            
            messages.success(request, 'Comprovante enviado com sucesso!')
            return redirect('settlement_list')
    else:
        form = SettlementUploadForm(order=order)
    
    return render(request, 'orders/upload_settlement.html', {'form': form, 'order': order})

@login_required
def settlement_list(request):
    user_distributor = getattr(request.user, 'distributor', None)
    
    if request.user.is_super_user_role():
        settlements = AccountSettlement.objects.all()
    elif user_distributor:
        settlements = AccountSettlement.objects.filter(order__target_distributor=user_distributor)
    else:
        settlements = AccountSettlement.objects.none()
        
    settlements = settlements.select_related('order').order_by('-created_at')
    
    return render(request, 'orders/settlement_list.html', {'settlements': settlements})

@login_required
def pending_payments(request):
    user_distributor = getattr(request.user, 'distributor', None)
    if not user_distributor:
        messages.error(request, "Apenas filiais podem acessar essa área.")
        return redirect('dashboard')
    
    # Orders ready for settlement: Confirmed/Delivered, Not Donation, Payment Pending/Partial
    orders = Order.objects.filter(
        target_distributor=user_distributor,
        status__in=['confirmado', 'entregue'],
    ).exclude(
        payment_condition=PaymentCondition.DOACAO
    ).exclude(
        payment_status=PaymentStatus.TOTAL
    ).order_by('-created_at')
    
    return render(request, 'orders/pending_payments.html', {'orders': orders})

@login_required
def audit_list(request):
    """
    Lista de aprovações pendentes para a Matriz.
    """
    if not request.user.is_superuser and not (hasattr(request.user, 'distributor') and request.user.distributor and request.user.distributor.tipo_unidade == 'MATRIZ'):
        messages.error(request, "Acesso restrito à Matriz.")
        return redirect('dashboard')
        
    # Filtrar apenas settlements não validados e sem motivo de recusa (pendentes reais)
    pending_settlements = AccountSettlement.objects.filter(
        is_validated=False,
        rejection_reason__isnull=True
    ).select_related('order', 'order__target_distributor').order_by('created_at')
    
    return render(request, 'orders/audit_list.html', {'settlements': pending_settlements})

from django.db import transaction
from django.db.models import Sum, Q, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils.dateparse import parse_date
from apps.stock.models import StockMovement, StockMovementType
from apps.products.models import ProductStock
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse

@login_required
# Relatórios de Fechamento (Reloading...)
def financial_closure_report(request):
    """
    Relatório de Fechamento de Caixa (Matriz).
    """
    try:
        # Verificar permissão: Apenas Staff/Matriz
        if not request.user.is_superuser and not (hasattr(request.user, 'distributor') and request.user.distributor and request.user.distributor.tipo_unidade == 'MATRIZ'):
            messages.error(request, "Acesso restrito à Matriz.")
            return redirect('dashboard')
            
        # Data do filtro (padrão: hoje)
        date_str = request.GET.get('date')
        if date_str:
            selected_date = parse_date(date_str)
        else:
            selected_date = timezone.now().date()
            
        if not selected_date:
            selected_date = timezone.now().date()

        # Filtro de pagamentos validados na data selecionada (usando created_at como proxy de entrada)
        settlements = AccountSettlement.objects.filter(
            is_validated=True,
            created_at__date=selected_date
        ).select_related('order', 'order__target_distributor', 'validated_by').order_by('-created_at')
        
        # 1. Total Recebido Hoje
        total_received = settlements.aggregate(
            total=Coalesce(Sum('value_reported', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
        
        # 2. Soma por Condição (Agrupado por PaymentCondition do Pedido)
        received_by_condition = settlements.values('order__payment_condition').annotate(
            total=Coalesce(Sum('value_reported', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        ).order_by('order__payment_condition')
        
        # 3. Soma por Filial
        received_by_branch = settlements.values('order__target_distributor__name').annotate(
            total=Coalesce(Sum('value_reported', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        ).order_by('order__target_distributor__name')
        
        # 4. Total Pendente Global (Tudo que ainda falta receber)
        # Pedidos confirmados/entregues que não estão quitados (PaymentStatus.TOTAL) e não são DOACAO
        # Calcular saldo devedor item a item para precisão
        orders_pending = Order.objects.exclude(
            payment_status=PaymentStatus.TOTAL
        ).exclude(
            payment_condition=PaymentCondition.DOACAO
        ).exclude(
            status__in=[OrderStatus.CANCELADO, OrderStatus.PENDENTE]
        ).annotate(
            paid=Coalesce(Sum('settlements__value_reported', filter=Q(settlements__is_validated=True), output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )
        
        total_pending_global = 0
        for o in orders_pending:
            paid_amount = o.paid or 0
            balance = o.total_amount - paid_amount
            if balance > 0:
                total_pending_global += balance

        # Determine base template for HTMX
        base_template = 'base_htmx.html' if request.htmx else 'base_full.html'

        context = {
            'selected_date': selected_date,
            'settlements': settlements,
            'total_received': total_received,
            'received_by_condition': received_by_condition,
            'received_by_branch': received_by_branch,
            'total_pending_global': total_pending_global,
            'base_template': base_template,
        }
        
        return render(request, 'orders/closure_report_final.html', context)
    except Exception as e:
        logger.error(f"Erro no relatório de fechamento: {str(e)}")
        traceback.print_exc()
        messages.error(request, f"Erro interno ao gerar relatório: {str(e)}")
        return redirect('dashboard')

@login_required
def export_closure_pdf(request):
    """
    Gera PDF do Relatório de Fechamento de Caixa.
    """
    try:
        # Verificar permissão: Apenas Staff/Matriz
        if not request.user.is_superuser and not (hasattr(request.user, 'distributor') and request.user.distributor and request.user.distributor.tipo_unidade == 'MATRIZ'):
            messages.error(request, "Acesso restrito à Matriz.")
            return redirect('dashboard')
            
        # Data do filtro (padrão: hoje)
        date_str = request.GET.get('date')
        if date_str:
            selected_date = parse_date(date_str)
        else:
            selected_date = timezone.now().date()
            
        if not selected_date:
            selected_date = timezone.now().date()

        # Filtro de pagamentos validados na data selecionada
        settlements = AccountSettlement.objects.filter(
            is_validated=True,
            created_at__date=selected_date
        ).select_related('order', 'order__target_distributor', 'validated_by').order_by('-created_at')
        
        # Totais
        total_received = settlements.aggregate(
            total=Coalesce(Sum('value_reported', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
        
        received_by_condition = settlements.values('order__payment_condition').annotate(
            total=Coalesce(Sum('value_reported', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        ).order_by('order__payment_condition')
        
        received_by_branch = settlements.values('order__target_distributor__name').annotate(
            total=Coalesce(Sum('value_reported', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        ).order_by('order__target_distributor__name')

        context = {
            'selected_date': selected_date,
            'settlements': settlements,
            'total_received': total_received,
            'received_by_condition': received_by_condition,
            'received_by_branch': received_by_branch,
            'user': request.user,
        }
        
        template_path = 'orders/closure_pdf.html'
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="fechamento_caixa_{selected_date}.pdf"'
        
        template = get_template(template_path)
        html = template.render(context)
        
        pisa_status = pisa.CreatePDF(
            html, dest=response
        )
        
        if pisa_status.err:
            return HttpResponse('Erro ao gerar PDF <pre>' + html + '</pre>')
            
        return response
    except Exception as e:
        logger.error(f"Erro ao exportar PDF: {str(e)}")
        traceback.print_exc()
        messages.error(request, f"Erro ao gerar PDF: {str(e)}")
        return redirect('financial_closure_report')

@login_required
def approve_settlement(request, pk):
    """
    Aprova um pagamento.
    """
    if not request.user.is_superuser and not (hasattr(request.user, 'distributor') and request.user.distributor and request.user.distributor.tipo_unidade == 'MATRIZ'):
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
        
    settlement = get_object_or_404(AccountSettlement, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Atualizar status do pedido
                order = settlement.order
                
                # Calcular novo saldo pendente considerando o pagamento atual como validado
                current_pending = order.pending_balance
                if not settlement.is_validated:
                    # Se ainda não foi validado, subtrai o valor reportado para simular o novo saldo
                    current_pending -= settlement.value_reported
                
                # Se o pagamento quitar o pedido, verificar estoque da Matriz ANTES de validar
                if current_pending <= 0:
                    # Verificar se há estoque suficiente na Matriz para todos os itens
                    # POOL: Se origem é MATRIZ, consolida estoque de todas as MATRIZes
                    is_origin_matriz = order.distributor and order.distributor.tipo_unidade == 'MATRIZ'
                    if is_origin_matriz:
                        all_matriz = Distributor.objects.filter(tipo_unidade='MATRIZ', is_active=True)
                    for item in order.items.all():
                        if is_origin_matriz:
                            total_stock = ProductStock.objects.filter(
                                product=item.product, distributor__in=all_matriz
                            ).aggregate(total=Sum('current_stock'))['total'] or 0
                            if total_stock < item.quantity:
                                raise ValueError(f"Estoque insuficiente na Sede para o produto {item.product.name}. Disponível: {total_stock}, Necessário: {item.quantity}")
                        else:
                            try:
                                matrix_stock = ProductStock.objects.get(product=item.product, distributor=order.distributor)
                                if matrix_stock.current_stock < item.quantity:
                                    raise ValueError(f"Estoque insuficiente na Sede para o produto {item.product.name}. Disponível: {matrix_stock.current_stock}, Necessário: {item.quantity}")
                            except ProductStock.DoesNotExist:
                                raise ValueError(f"Produto {item.product.name} não encontrado no estoque da Sede.")

                # Se passou pela verificação, validar o pagamento
                settlement.is_validated = True
                settlement.validated_by = request.user
                settlement.rejection_reason = None # Limpar recusa se houver
                settlement.save()
                
                # Atualizar status do pedido
                if current_pending <= 0:
                    order.payment_status = PaymentStatus.TOTAL
                    
                    # Realizar transferência de estoque
                    all_matriz_dists = Distributor.objects.filter(tipo_unidade='MATRIZ', is_active=True) if is_origin_matriz else None
                    for item in order.items.all():
                        # 1. Decrementar do Pool de MATRIZes (FIFO por validade)
                        if is_origin_matriz:
                            matriz_stocks = ProductStock.objects.filter(
                                product=item.product, distributor__in=all_matriz_dists, current_stock__gt=0
                            ).order_by('expiration_date', 'updated_at')
                        else:
                            matriz_stocks = ProductStock.objects.filter(
                                product=item.product, distributor=order.distributor, current_stock__gt=0
                            ).order_by('expiration_date', 'updated_at')

                        remaining = item.quantity
                        for matrix_stock in matriz_stocks:
                            if remaining <= 0:
                                break
                            deduct = min(matrix_stock.current_stock, remaining)
                            previous_matrix = matrix_stock.current_stock
                            matrix_stock.current_stock -= deduct
                            matrix_stock.save()
                            remaining -= deduct

                            # Log Saída Matriz
                            StockMovement.objects.create(
                                distributor=matrix_stock.distributor,
                                product=item.product,
                                movement_type=StockMovementType.TRANSFER_OUT,
                                quantity=deduct,
                                previous_stock=previous_matrix,
                                new_stock=matrix_stock.current_stock,
                                reason=f"Gerado automaticamente pela liquidação do Pedido #{order.order_number}",
                                reference_id=order.id,
                                reference_type='order',
                                user=request.user
                            )
                        
                        # (Log Saída Matriz já feito dentro do loop acima)
                        
                        # 2. Incrementar na Filial (com batch único de transferência)
                        transfer_batch = f'TRANSF-{order.order_number}'
                        filial_stock, created = ProductStock.objects.get_or_create(
                            product=item.product,
                            distributor=order.target_distributor,
                            batch=transfer_batch,
                            defaults={'current_stock': 0}
                        )
                        previous_filial = filial_stock.current_stock
                        filial_stock.current_stock += item.quantity
                        filial_stock.save()
                        
                        # Log Entrada Filial
                        StockMovement.objects.create(
                            distributor=order.target_distributor,
                            product=item.product,
                            movement_type=StockMovementType.TRANSFER_IN,
                            quantity=item.quantity,
                            batch=transfer_batch,
                            previous_stock=previous_filial,
                            new_stock=filial_stock.current_stock,
                            reason=f"Gerado automaticamente pela liquidação do Pedido #{order.order_number}",
                            reference_id=order.id,
                            reference_type='order',
                            user=request.user
                        )
                    
                    messages.success(request, f"Pedido {order.order_number} liquidado! Estoque transferido da Sede para {order.target_distributor.name}.")
                else:
                    order.payment_status = PaymentStatus.PARCIAL
                    messages.success(request, f"Pagamento validado. Pedido {order.order_number} parcialmente pago.")
                
                order.save()
                
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('financial_audit_list')
        except Exception as e:
            messages.error(request, f"Erro ao processar validação: {str(e)}")
            return redirect('financial_audit_list')
            
        return redirect('financial_audit_list')
        
    return redirect('financial_audit_list')

@login_required
def reject_settlement(request, pk):
    """
    Recusa um pagamento.
    """
    if not request.user.is_superuser and not (hasattr(request.user, 'distributor') and request.user.distributor and request.user.distributor.tipo_unidade == 'MATRIZ'):
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
        
    settlement = get_object_or_404(AccountSettlement, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason')
        if not reason:
            messages.error(request, "Informe o motivo da recusa.")
            return redirect('audit_list')
            
        settlement.is_validated = False
        settlement.validated_by = request.user
        settlement.rejection_reason = reason
        settlement.save()
        
        messages.warning(request, f"Pagamento recusado. Motivo registrado.")
        return redirect('financial_audit_list')
        
    return redirect('financial_audit_list')
