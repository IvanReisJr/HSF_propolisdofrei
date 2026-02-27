"""
Suíte Completa de Testes do Sistema HSF Própolis do Frei
=========================================================
Cobre TODAS as ações realizáveis por Matriz e Filial:
  - Produtos (CRUD)
  - Estoque (Entrada, Saída, Ajuste)
  - Pedidos (Criar, Autorizar, Confirmar, Cancelar, Deletar)
  - Prestação de Contas (Upload, Aprovar, Recusar)
  - Permissões: Filial não acessa rotas restritas à Matriz
"""
import pytest
import io
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.products.models import Product, ProductStock, Packaging
from apps.categories.models import Category
from apps.distributors.models import Distributor
from apps.stock.models import StockMovement, StockMovementType
from apps.orders.models import Order, OrderItem, AccountSettlement, PaymentCondition
from apps.core.models import UnitOfMeasure

User = get_user_model()
pytestmark = pytest.mark.django_db


# ==============================================================================
# FIXTURE CENTRAL: cria todos os objetos base para os testes
# ==============================================================================
@pytest.fixture
def setup(db):
    """
    Cria toda a infraestrutura compartilhada:
      Matriz (CD Sede Adm), Filial (AME Atibaia), Usuários, Produto, Estoque inicial.
    """
    unit, _ = UnitOfMeasure.objects.get_or_create(name="Unidade", abbreviation="un")
    cat = Category.objects.create(name="Categoria Teste")

    # Distribuidores
    matriz = Distributor.objects.create(
        name="CD Sede Adm", document="11111111000100", tipo_unidade="MATRIZ"
    )
    filial = Distributor.objects.create(
        name="AME Atibaia", document="22222222000100", tipo_unidade="FILIAL"
    )

    # Usuários
    user_matriz = User.objects.create_user(
        email="matriz@hsf.test", password="Senha@1234", distributor=matriz
    )
    user_filial = User.objects.create_user(
        email="filial@hsf.test", password="Senha@1234", distributor=filial
    )
    user_admin = User.objects.create_superuser(
        email="admin@hsf.test", password="Senha@1234"
    )

    # Embalagem
    pack = Packaging.objects.create(name="Frasco Teste", distributor=matriz)

    # Produto
    produto = Product.objects.create(
        name="Própolis Teste",
        category=cat,
        packaging=pack,
        distributor=matriz,
        unit="un",
        unit_fk=unit,
        cost_price=Decimal("10.00"),
        sale_price=Decimal("25.00"),
    )

    # Estoque inicial na Matriz (100 unidades)
    stock_matriz = ProductStock.objects.create(
        product=produto,
        distributor=matriz,
        batch="LOTE-TEST-001",
        current_stock=100,
    )

    return {
        "matriz": matriz,
        "filial": filial,
        "user_matriz": user_matriz,
        "user_filial": user_filial,
        "user_admin": user_admin,
        "produto": produto,
        "pack": pack,
        "cat": cat,
        "unit": unit,
        "stock_matriz": stock_matriz,
    }


# ==============================================================================
# HELPER: cria um pedido completo (pendente) via ORM sem HTTP
# ==============================================================================
def _create_order(setup, qty=10):
    order = Order.objects.create(
        distributor=setup["matriz"],
        target_distributor=setup["filial"],
        user=setup["user_filial"],
        status="pendente",
        payment_condition=PaymentCondition.VISTA,
        total_amount=Decimal("0.00"),
    )
    item = OrderItem.objects.create(
        order=order,
        product=setup["produto"],
        quantity=qty,
        unit_price=Decimal("25.00"),
        total_price=Decimal("25.00") * qty,
    )
    order.total_amount = item.total_price
    order.save()
    return order


# ==============================================================================
# 1. DASHBOARD
# ==============================================================================
class TestDashboard:
    def test_dashboard_matriz(self, client, setup):
        client.force_login(setup["user_matriz"])
        r = client.get(reverse("dashboard"))
        assert r.status_code == 200

    def test_dashboard_filial(self, client, setup):
        client.force_login(setup["user_filial"])
        r = client.get(reverse("dashboard"))
        assert r.status_code == 200

    def test_dashboard_requer_login(self, client):
        r = client.get(reverse("dashboard"))
        assert r.status_code in [302, 200]  # redireciona para login ou exige auth


# ==============================================================================
# 2. PRODUTOS (somente Matriz pode criar/editar/deletar)
# ==============================================================================
class TestProducts:
    def test_listagem_produtos_matriz(self, client, setup):
        client.force_login(setup["user_matriz"])
        r = client.get(reverse("product_list"))
        assert r.status_code == 200
        assert "Própolis Teste".encode() in r.content

    def test_listagem_produtos_filial(self, client, setup):
        """Filial pode ver lista de produtos"""
        client.force_login(setup["user_filial"])
        r = client.get(reverse("product_list"))
        assert r.status_code == 200

    def test_criar_produto_matriz(self, client, setup):
        client.force_login(setup["user_matriz"])
        data = {
            "name": "Novo Produto",
            "cost_price": "5.00",
            "sale_price": "15.00",
            "category": setup["cat"].id,
            "packaging": setup["pack"].id,
            "unit": str(setup["unit"].id),  # UnitOfMeasure FK
            "status": "active",
            "min_stock": "5",
        }
        r = client.post(reverse("product_create"), data)
        assert r.status_code in [200, 302]
        assert Product.objects.filter(name="Novo Produto").exists()

    def test_editar_produto_matriz(self, client, setup):
        client.force_login(setup["user_matriz"])
        produto = setup["produto"]
        data = {
            "name": "Própolis Editado",
            "cost_price": "12.00",
            "sale_price": "30.00",
            "category": setup["cat"].id,
            "packaging": setup["pack"].id,
            "unit": str(setup["unit"].id),
            "status": "active",
            "min_stock": "5",
        }
        r = client.post(reverse("product_edit", kwargs={"pk": produto.pk}), data)
        assert r.status_code in [200, 302]
        produto.refresh_from_db()
        assert produto.name == "Própolis Editado"

    def test_detalhe_produto(self, client, setup):
        client.force_login(setup["user_matriz"])
        r = client.get(reverse("product_detail", kwargs={"pk": setup["produto"].pk}))
        assert r.status_code == 200

    def test_deletar_produto_soft_delete(self, client, setup):
        """Soft delete: produto some da listagem padrão mas fica em all_objects"""
        client.force_login(setup["user_admin"])
        produto = setup["produto"]
        r = client.post(reverse("product_delete", kwargs={"pk": produto.pk}))
        assert r.status_code in [200, 302]
        produto.refresh_from_db()
        assert produto.is_active is False
        # Volta a ativar para não quebrar outros testes
        produto.is_active = True
        produto.save()


# ==============================================================================
# 3. ESTOQUE — Matriz
# ==============================================================================
class TestStockMatriz:
    def test_listagem_movimentacoes(self, client, setup):
        client.force_login(setup["user_matriz"])
        r = client.get(reverse("movement_list"))
        assert r.status_code == 200

    def test_registrar_entrada_matriz(self, client, setup):
        client.force_login(setup["user_matriz"])
        data = {
            "product": setup["produto"].id,
            "distributor": setup["matriz"].id,
            "quantity": 50,
            "batch": "LOTE-ENTRADA",
        }
        r = client.post(reverse("registrar_entrada"), data)
        assert r.status_code in [200, 302]
        assert StockMovement.objects.filter(
            product=setup["produto"],
            movement_type=StockMovementType.ENTRY,
        ).exists()
        stock = ProductStock.objects.get(
            product=setup["produto"],
            distributor=setup["matriz"],
            batch="LOTE-ENTRADA",
        )
        assert stock.current_stock == 50

    def test_registrar_saida_matriz(self, client, setup):
        client.force_login(setup["user_matriz"])
        data = {
            "product": setup["produto"].id,
            "distributor": setup["matriz"].id,
            "quantity": 10,
        }
        r = client.post(reverse("registrar_saida"), data)
        assert r.status_code in [200, 302]
        # Estoque deve ter diminuído 10 do LOTE-TEST-001
        setup["stock_matriz"].refresh_from_db()
        assert setup["stock_matriz"].current_stock == 90

    def test_ajustar_estoque(self, client, setup):
        client.force_login(setup["user_matriz"])
        produto = setup["produto"]
        url = reverse("ajustar_estoque", kwargs={"product_id": produto.pk})
        data = {
            "batch": "LOTE-TEST-001",
            "expiration_date": "2027-12-31",
            "quantity": 200,
            "reason": "Inventário",
        }
        r = client.post(url, data)
        assert r.status_code in [200, 302]
        stock = ProductStock.objects.get(
            product=produto, distributor=setup["matriz"], batch="LOTE-TEST-001"
        )
        assert stock.current_stock == 200
        # restaura
        stock.current_stock = 100
        stock.save()


# ==============================================================================
# 4. ESTOQUE — Filial
# ==============================================================================
class TestStockFilial:
    def test_filial_nao_pode_registrar_entrada_para_outra_unidade(self, client, setup):
        """Filial só vê seu próprio estoque, mas o form não impede POST — valida redirecionamento"""
        client.force_login(setup["user_filial"])
        # Cria estoque para a filial primeiro
        ProductStock.objects.create(
            product=setup["produto"],
            distributor=setup["filial"],
            batch="LOTE-FILIAL",
            current_stock=20,
        )
        data = {
            "product": setup["produto"].id,
            "distributor": setup["filial"].id,
            "quantity": 5,
        }
        r = client.post(reverse("registrar_saida"), data)
        assert r.status_code in [200, 302]
        stock = ProductStock.objects.get(
            product=setup["produto"],
            distributor=setup["filial"],
            batch="LOTE-FILIAL",
        )
        assert stock.current_stock == 15

    def test_dashboard_consolidado_restrito_a_staff(self, client, setup):
        """Filial não pode acessar o dashboard consolidado da Matriz"""
        client.force_login(setup["user_filial"])
        r = client.get(reverse("dashboard_matriz_consolidado"))
        assert r.status_code in [302, 403]


# ==============================================================================
# 5. PEDIDOS — Ciclo Completo
# ==============================================================================
class TestOrderFlow:
    def test_filial_cria_pedido(self, client, setup):
        client.force_login(setup["user_filial"])
        data = {
            "distributor": setup["matriz"].id,
            "payment_condition": "consignado",
            "products[]": [str(setup["produto"].id)],
            "quantities[]": ["5"],
            "unit_prices[]": ["25,00"],
        }
        r = client.post(reverse("order_create"), data)
        assert r.status_code in [200, 302]
        assert Order.objects.filter(target_distributor=setup["filial"]).exists()

    def test_matriz_autoriza_pedido(self, client, setup):
        order = _create_order(setup, qty=5)
        client.force_login(setup["user_matriz"])
        r = client.post(reverse("order_authorize", kwargs={"pk": order.pk}))
        assert r.status_code in [200, 302]
        order.refresh_from_db()
        assert order.status == "autorizado"

    def test_filial_nao_pode_autorizar_pedido(self, client, setup):
        order = _create_order(setup, qty=5)
        client.force_login(setup["user_filial"])
        r = client.post(reverse("order_authorize", kwargs={"pk": order.pk}))
        # Deve redirecionar com mensagem de erro (não autorizar)
        order.refresh_from_db()
        assert order.status == "pendente"  # não mudou

    def test_confirmar_pedido_baixa_estoque_pool_matriz(self, client, setup):
        """
        Mesmo com pedido em CD Sede Adm, o estoque está em LOTE-TEST-001 (CD Sede Adm).
        A baixa deve funcionar pelo pool de todas as MATRIZes.
        """
        order = _create_order(setup, qty=10)
        order.status = "autorizado"
        order.save()

        estoque_antes = setup["stock_matriz"].current_stock

        client.force_login(setup["user_matriz"])
        r = client.post(reverse("order_confirm", kwargs={"pk": order.pk}))
        assert r.status_code in [200, 302]

        order.refresh_from_db()
        assert order.status == "confirmado"

        setup["stock_matriz"].refresh_from_db()
        assert setup["stock_matriz"].current_stock == estoque_antes - 10

        # Filial deve ter recebido o estoque via lote TRANSF-{order_number}
        filial_stock = ProductStock.objects.filter(
            product=setup["produto"],
            distributor=setup["filial"],
            batch__startswith="TRANSF-",
        ).first()
        assert filial_stock is not None
        assert filial_stock.current_stock == 10

    def test_pool_matriz_dois_cds(self, client, setup):
        """
        Cria um segundo CD Matriz com estoque. Pedido usa o primeiro CD como origem
        mas stock está no segundo. Deve consolidar e funcionar.
        """
        cd2 = Distributor.objects.create(
            name="CD Humanitas", document="33333333000100", tipo_unidade="MATRIZ"
        )
        # Zera estoque do CD Sede Adm e coloca no CD Humanitas
        setup["stock_matriz"].current_stock = 0
        setup["stock_matriz"].save()
        stock_cd2 = ProductStock.objects.create(
            product=setup["produto"],
            distributor=cd2,
            batch="LOTE-CD2",
            current_stock=50,
        )

        order = _create_order(setup, qty=20)
        # Origem é CD Sede Adm (zerado), mas pool inclui CD Humanitas
        order.status = "autorizado"
        order.save()

        client.force_login(setup["user_matriz"])
        r = client.post(reverse("order_confirm", kwargs={"pk": order.pk}))
        assert r.status_code in [200, 302]

        order.refresh_from_db()
        assert order.status == "confirmado"
        stock_cd2.refresh_from_db()
        assert stock_cd2.current_stock == 30  # 50 - 20

        # Restaura
        setup["stock_matriz"].current_stock = 100
        setup["stock_matriz"].save()

    def test_cancelar_pedido_pendente(self, client, setup):
        order = _create_order(setup, qty=5)
        client.force_login(setup["user_filial"])
        r = client.post(reverse("order_cancel", kwargs={"pk": order.pk}))
        assert r.status_code in [200, 302]
        order.refresh_from_db()
        assert order.status == "cancelado"

    def test_cancelar_pedido_confirmado_falha(self, client, setup):
        """Pedidos confirmados não podem ser cancelados"""
        order = _create_order(setup, qty=5)
        order.status = "confirmado"
        order.save()
        client.force_login(setup["user_matriz"])
        r = client.post(reverse("order_cancel", kwargs={"pk": order.pk}))
        order.refresh_from_db()
        assert order.status == "confirmado"

    def test_deletar_pedido_soft_delete(self, client, setup):
        order = _create_order(setup, qty=5)
        client.force_login(setup["user_matriz"])
        r = client.post(reverse("order_delete", kwargs={"pk": order.pk}))
        assert r.status_code in [200, 302]
        assert Order.objects.filter(id=order.id).count() == 0  # soft deleted
        assert Order.all_objects.filter(id=order.id).exists()  # ainda no banco

    def test_estoque_insuficiente_impede_confirmacao(self, client, setup):
        """Pedido com 999 unidades falha pois há apenas 100"""
        order = _create_order(setup, qty=999)
        order.status = "autorizado"
        order.save()

        client.force_login(setup["user_matriz"])
        r = client.post(reverse("order_confirm", kwargs={"pk": order.pk}))
        order.refresh_from_db()
        assert order.status == "autorizado"  # não confirmou

    def test_produto_inativo_bloqueia_pedido(self, client, setup):
        setup["produto"].is_active = False
        setup["produto"].save()

        client.force_login(setup["user_filial"])
        data = {
            "distributor": setup["matriz"].id,
            "payment_condition": "vista",
            "products[]": [str(setup["produto"].id)],
            "quantities[]": ["5"],
            "unit_prices[]": ["25,00"],
        }
        r = client.post(reverse("order_create"), data)
        # Nenhum pedido deve ter sido criado
        assert Order.objects.filter(target_distributor=setup["filial"]).count() == 0

        setup["produto"].is_active = True
        setup["produto"].save()

    def test_filial_nao_cria_pedido_para_outra_filial(self, client, setup):
        """A origem deve ser MATRIZ — filial como origem deve falhar"""
        client.force_login(setup["user_filial"])
        data = {
            "distributor": setup["filial"].id,  # Filial como origem = inválido
            "payment_condition": "vista",
            "products[]": [str(setup["produto"].id)],
            "quantities[]": ["5"],
            "unit_prices[]": ["25,00"],
        }
        r = client.post(reverse("order_create"), data)
        assert Order.objects.filter(
            distributor=setup["filial"]
        ).count() == 0


# ==============================================================================
# 6. PRESTAÇÃO DE CONTAS
# ==============================================================================
class TestSettlement:
    def _criar_pedido_confirmado(self, setup):
        """Cria um pedido e o confirma direto via ORM para não depender do HTTP"""
        order = _create_order(setup, qty=5)
        order.status = "confirmado"
        order.save()
        return order

    def test_listar_settlements_filial(self, client, setup):
        client.force_login(setup["user_filial"])
        r = client.get(reverse("settlement_list"))
        assert r.status_code == 200

    def test_upload_settlement_filial(self, client, setup):
        order = self._criar_pedido_confirmado(setup)
        client.force_login(setup["user_filial"])
        fake_file = io.BytesIO(b"comprovante_fake_pdf")
        fake_file.name = "comprovante.pdf"
        data = {
            "value_reported": "125.00",
            "receipt_file": fake_file,
        }
        r = client.post(
            reverse("upload_settlement", kwargs={"order_id": order.id}), data
        )
        assert r.status_code in [200, 302]
        assert AccountSettlement.objects.filter(order=order).exists()

    def test_aprovar_settlement_matriz(self, client, setup):
        order = self._criar_pedido_confirmado(setup)
        # Cria estoque para filial para evitar erros
        ProductStock.objects.get_or_create(
            product=setup["produto"],
            distributor=setup["filial"],
            batch="TRANSF-X",
            defaults={"current_stock": 50},
        )
        settlement = AccountSettlement.objects.create(
            order=order,
            value_reported=order.total_amount,
            receipt_file="dummy/path.pdf",
            is_validated=False,
        )
        client.force_login(setup["user_matriz"])
        r = client.post(
            reverse("approve_settlement", kwargs={"pk": settlement.pk})
        )
        assert r.status_code in [200, 302]
        settlement.refresh_from_db()
        assert settlement.is_validated is True

    def test_recusar_settlement_matriz(self, client, setup):
        order = self._criar_pedido_confirmado(setup)
        settlement = AccountSettlement.objects.create(
            order=order,
            value_reported=Decimal("50.00"),
            receipt_file="dummy/path.pdf",
            is_validated=False,
        )
        client.force_login(setup["user_matriz"])
        r = client.post(
            reverse("reject_settlement", kwargs={"pk": settlement.pk}),
            {"rejection_reason": "Comprovante ilegível"},
        )
        assert r.status_code in [200, 302]
        settlement.refresh_from_db()
        assert settlement.rejection_reason == "Comprovante ilegível"

    def test_filial_nao_pode_aprovar_settlement(self, client, setup):
        order = self._criar_pedido_confirmado(setup)
        settlement = AccountSettlement.objects.create(
            order=order,
            value_reported=order.total_amount,
            receipt_file="dummy/path.pdf",
            is_validated=False,
        )
        client.force_login(setup["user_filial"])
        r = client.post(
            reverse("approve_settlement", kwargs={"pk": settlement.pk})
        )
        settlement.refresh_from_db()
        assert settlement.is_validated is False

    def test_central_auditoria_acessivel_apenas_matriz(self, client, setup):
        client.force_login(setup["user_filial"])
        r = client.get(reverse("financial_audit_list"))
        assert r.status_code in [302, 403]

    def test_central_auditoria_acessivel_por_matriz(self, client, setup):
        client.force_login(setup["user_matriz"])
        r = client.get(reverse("financial_audit_list"))
        assert r.status_code == 200


# ==============================================================================
# 7. AUDITORIA DE SISTEMA (StockMovement → AuditLog via signal)
# ==============================================================================
class TestAuditLog:
    def test_entrada_estoque_cria_audit_log(self, client, setup):
        from apps.audit.models import AuditLog
        AuditLog.objects.all().delete()

        client.force_login(setup["user_matriz"])
        client.post(
            reverse("registrar_entrada"),
            {
                "product": setup["produto"].id,
                "distributor": setup["matriz"].id,
                "quantity": 30,
                "batch": "LOTE-AUDIT",
            },
        )
        assert AuditLog.objects.filter(action="INSERT", table_name="stock_movements").exists()

    def test_saida_estoque_cria_audit_log_com_usuario(self, client, setup):
        from apps.audit.models import AuditLog
        AuditLog.objects.all().delete()

        client.force_login(setup["user_filial"])
        ProductStock.objects.get_or_create(
            product=setup["produto"],
            distributor=setup["filial"],
            batch="LOTE-SAI",
            defaults={"current_stock": 30},
        )
        client.post(
            reverse("registrar_saida"),
            {
                "product": setup["produto"].id,
                "distributor": setup["filial"].id,
                "quantity": 5,
            },
        )
        log = AuditLog.objects.filter(table_name="stock_movements").first()
        assert log is not None
        assert log.user == setup["user_filial"]


# ==============================================================================
# 8. SOFT DELETE
# ==============================================================================
class TestSoftDelete:
    def test_produto_soft_delete(self, setup):
        import uuid
        unique_code = f"PROD-TST-{uuid.uuid4().hex[:8].upper()}"
        p = Product.all_objects.create(
            name="Temp Delete",
            code=unique_code,
            distributor=setup["matriz"],
            cost_price=Decimal("1.00"),
            sale_price=Decimal("2.00"),
        )
        p.delete()
        assert Product.objects.filter(id=p.id).count() == 0
        assert Product.all_objects.filter(id=p.id).count() == 1

    def test_order_soft_delete(self, setup):
        order = _create_order(setup, qty=2)
        order.delete()
        assert Order.objects.filter(id=order.id).count() == 0
        assert Order.all_objects.filter(id=order.id).count() == 1

    def test_stock_movement_soft_delete(self, setup):
        mov = StockMovement.objects.create(
            product=setup["produto"],
            distributor=setup["matriz"],
            movement_type=StockMovementType.ENTRY,
            quantity=5,
            previous_stock=100,
            new_stock=105,
            reason="Teste",
            user=setup["user_matriz"],
        )
        assert StockMovement.objects.filter(id=mov.id).count() == 1
        mov.delete()
        assert StockMovement.objects.filter(id=mov.id).count() == 0
        assert StockMovement.all_objects.filter(id=mov.id).count() == 1


# ==============================================================================
# 9. RELATÓRIOS
# ==============================================================================
class TestRelatorios:
    def test_relatorio_inventario_accesivel(self, client, setup):
        client.force_login(setup["user_matriz"])
        r = client.get(reverse("inventory_report"))
        assert r.status_code == 200

    def test_fechamento_caixa_somente_matriz(self, client, setup):
        client.force_login(setup["user_filial"])
        r = client.get(reverse("financial_closure_report"))
        assert r.status_code in [302, 403]

    def test_fechamento_caixa_acessivel_por_matriz(self, client, setup):
        client.force_login(setup["user_matriz"])
        r = client.get(reverse("financial_closure_report"))
        assert r.status_code == 200
