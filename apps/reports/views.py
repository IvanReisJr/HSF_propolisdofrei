from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.products.models import ProductStock
from apps.distributors.models import Distributor
from django.db.models import Sum, F
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils.text import slugify
from django.utils import timezone
from xhtml2pdf import pisa
import io

@login_required
def inventory_report(request):
    """
    Relatório de Inventário (HTML).
    """
    user = request.user
    is_matriz = user.is_superuser or (user.distributor and user.distributor.tipo_unidade == 'MATRIZ')
    
    if is_matriz:
        stocks = ProductStock.objects.select_related('product', 'distributor').order_by('distributor__name', 'product__name')
    else:
        if user.distributor:
            stocks = ProductStock.objects.filter(distributor=user.distributor).select_related('product', 'distributor').order_by('product__name')
        else:
            stocks = ProductStock.objects.none()

    context = {
        'stocks': stocks,
        'is_matriz': is_matriz,
        'page_title': 'Relatório de Inventário'
    }
    return render(request, 'reports/inventory_report.html', context)

@login_required
def inventory_pdf(request):
    """
    Gera PDF do Relatório de Inventário.
    """
    user = request.user
    is_matriz = user.is_superuser or (user.distributor and user.distributor.tipo_unidade == 'MATRIZ')
    
    # Filter Logic
    if is_matriz:
        # Check if we are simulating a distributor (optional, but good for consistency)
        simulated_id = request.session.get('simulated_distributor_id')
        if simulated_id:
            stocks = ProductStock.objects.filter(distributor_id=simulated_id).select_related('product', 'distributor').order_by('product__name')
            # Fetch name for filename
            dist_name = Distributor.objects.filter(id=simulated_id).values_list('name', flat=True).first()
            filename_unit = dist_name if dist_name else "Simulacao"
            report_subtitle = f"Visão Simulada: {filename_unit}"
        else:
            stocks = ProductStock.objects.select_related('product', 'distributor').order_by('distributor__name', 'product__name')
            report_subtitle = "Visão Geral (Matriz)"
            filename_unit = "Matriz_Geral"
    else:
        if user.distributor:
            stocks = ProductStock.objects.filter(distributor=user.distributor).select_related('product', 'distributor').order_by('product__name')
            report_subtitle = f"Unidade: {user.distributor.name}"
            filename_unit = user.distributor.name
        else:
            stocks = ProductStock.objects.none()
            report_subtitle = "Sem Unidade Vinculada"
            filename_unit = "Sem_Unidade"

    # Specific requirement check: "Extrato de Própolis 30ml"
    # We don't filter *only* this, but we ensure it's in the list if it exists.
    # The QuerySet gets all stocks.
    
    context = {
        'stocks': stocks,
        'is_matriz': is_matriz,
        'report_subtitle': report_subtitle,
        'user': user,
    }
    
    template_path = 'reports/inventory_pdf.html'
    
    template = get_template(template_path)
    html = template.render(context)
    
    # Create a byte stream buffer
    buffer = io.BytesIO()
    
    # Create the PDF object, using the buffer as its "file."
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    
    # If there was an error
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
        
    # Get the value of the BytesIO buffer and write it to the response.
    buffer.seek(0)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    # Force download or view
    current_date = timezone.now().strftime('%d-%m-%Y')
    safe_unit_name = slugify(filename_unit)
    filename = f"Inventario_{safe_unit_name}_{current_date}.pdf"
    
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response
