from django.db import transaction
from apps.products.models import Product, ProductStock
from apps.distributors.models import Distributor
from apps.stock.models import StockMovement

def run():
    """
    Ponto de entrada para o comando runscript.
    Recalcula o saldo de um produto específico em um distribuidor.
    """
    # --- PARÂMETROS PARA CORREÇÃO ---
    # Substitua com os nomes exatos do produto e da unidade
    product_name = "Café - Pacote: 500 g - Em Grão - BR" 
    distributor_name = "AME Atibaia"
    # ---------------------------------

    try:
        product = Product.objects.get(name__iexact=product_name)
        distributor = Distributor.objects.get(name__iexact=distributor_name)
    except (Product.DoesNotExist, Distributor.DoesNotExist) as e:
        print(f"Erro: {e}")
        return

    # Agrupa por lote para recalcular cada ProductStock individualmente
    movements_por_lote = StockMovement.objects.filter(
        product=product,
        distributor=distributor
    ).values('batch').distinct()

    print(f"Recalculando saldos para o produto '{product.name}' na unidade '{distributor.name}'...")

    for item in movements_por_lote:
        # Se o lote do banco for None, usamos 'SEM LOTE' para o ProductStock
        db_batch = item['batch']
        stock_batch = db_batch if db_batch is not None else 'SEM LOTE'
        
        # Filtra os movimentos para o lote específico (None ou não)
        movements = StockMovement.objects.filter(
            product=product,
            distributor=distributor,
            batch=db_batch
        ).order_by('created_at')

        if not movements.exists():
            continue

        saldo_calculado = 0
        for mov in movements:
            if mov.movement_type in ['entry', 'adjustment_plus', 'reversal_out']:
                saldo_calculado += mov.quantity
            elif mov.movement_type in ['exit', 'adjustment_minus', 'reversal_in']:
                saldo_calculado -= mov.quantity
        
        # Garante que o saldo não seja negativo
        saldo_calculado = max(0, saldo_calculado)

        try:
            with transaction.atomic():
                # Usa 'stock_batch' que nunca é None
                stock, created = ProductStock.objects.update_or_create(
                    product=product,
                    distributor=distributor,
                    batch=stock_batch,
                    defaults={'current_stock': saldo_calculado}
                )
                
                if created:
                    print(f"  - Lote '{stock_batch}' (original: {db_batch}): Criado com saldo {saldo_calculado}.")
                else:
                    print(f"  - Lote '{stock_batch}' (original: {db_batch}): Saldo atualizado para {saldo_calculado}.")

        except Exception as e:
            print(f"  - Lote '{stock_batch}' (original: {db_batch}): ERRO ao atualizar o saldo. Transação revertida. Detalhes: {e}")

    print("\nRecálculo concluído.")
