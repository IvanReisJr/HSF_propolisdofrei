Aqui está o Relatório de Arquitetura Técnica baseado na análise estática do código e documentação fornecidos.

Relatório de Arquitetura Técnica - Projeto HSF_PROPOLISDOFREI
Data: 05/02/2026 Responsável: Gemini Code Assist (Atuando como Arquiteto de Sistemas) Contexto: Análise dos módulos products, documentação de arquitetura e changelogs recentes.

1. Definição de Modelos (Principais Campos)
Com base em apps/products/models.py e referências na documentação:

Produto (Product)
Identificação: id (UUID, PK), code (String, Único, Gerado Automaticamente).
Relacionamentos:
category (FK -> Category)
packaging (FK -> Packaging)
distributor (FK -> Distributor, representa a "Matriz proprietária").
unit_fk (FK -> UnitOfMeasure).
Dados Financeiros/Logísticos: cost_price, sale_price, min_stock.
Controle: status (Active/Inactive), is_active (Soft Delete).
Distribuidor (Distributor)
(Inferido via referências e Changelog, arquivo de modelo não fornecido no contexto)

Campos Prováveis: id, name, distributor_type (Matriz/Filial), is_active.
Estoque (ProductStock)
Chaves: id (UUID).
Vínculos:
product (FK).
distributor (FK - Novo padrão de isolamento).
establishment (FK - Depreciado/Nullable, mantido para transição).
Dados: current_stock (Inteiro), batch (Lote), expiration_date.
Constraint: UniqueConstraint em ['product', 'distributor', 'batch'].
Pedido (Order)
(Baseado em CHANGELOG.md e ARCHITECTURE.md)

Identificação: order_number (Formato PED-YYYYMMDD-NNNN).
Fluxo:
distributor (Destino/Filial).
target_distributor (Origem/Matriz - CD de onde sai o estoque).
Estado: status (Pendente, Confirmado, Cancelado).
2. Fluxo de Estoque (Saída de Mercadoria)
Análise: O código fonte da View de saída (provavelmente em apps/orders ou apps/stock) não está presente no contexto fornecido.

Comportamento Documentado (ARCHITECTURE.md):

Gatilho: A subtração ocorre na confirmação do Pedido (Order).
Lógica: O sistema verifica o saldo em ProductStock.
Subtração: current_stock -= qty.
Registro: Gera um StockMovement com tipo 'exit'.
Observação Crítica: A documentação menciona que a entrada (registrar_entrada) usa transaction.atomic e filtra por Distribuidor. Assume-se que a saída siga o mesmo padrão para garantir integridade, utilizando o ID da Matriz (Origem) para localizar o lote correto, mas isso não pode ser validado via código neste momento.

3. Estado dos Templates (Formulários)
Listagem baseada nas referências encontradas em apps/products/views.py.

Módulo products (Confirmados)
products/product_list_v2.html (Listagem)
products/product_form.html (Criação e Edição de Produtos)
products/product_confirm_delete.html (Confirmação de Inativação)
products/product_detail.html (Visualização Detalhada)
products/packaging_list.html (Listagem de Embalagens)
products/packaging_form.html (Criação e Edição de Embalagens)
products/packaging_confirm_delete.html (Inativação de Embalagens)
Módulo orders
Status: Arquivos não visíveis no contexto.
Referência: O CHANGELOG.md menciona correções em order_detail.html. Espera-se a existência de order_form.html e order_list.html seguindo o padrão do projeto.
4. Dificuldades e Riscos (Integridade de Dados)
Imutabilidade de PK/Código
Situação Atual:
Product.id: Seguro (editable=False no model).
Product.code: Risco Identificado. No models.py, o campo é definido como models.CharField(..., unique=True), mas não possui editable=False.
Mitigação Atual: A proteção existe apenas na camada de View (product_edit em views.py), onde a lógica ignora explicitamente o dado vindo do POST para este campo.
Recomendação: Se o campo code for alterado via Django Admin ou Shell, não há bloqueio no nível do banco/modelo. Recomenda-se adicionar editable=False ao modelo se a regra de negócio for estrita, ou manter como está se houver casos raros de correção manual via Admin.
Transição de Estoque
O modelo ProductStock ainda possui o campo establishment (nullable). É crucial garantir que todas as novas Views (como a de Pedidos) estejam gravando e lendo exclusivamente do campo distributor para evitar inconsistência de dados durante a fase de transição ("Fase 02").