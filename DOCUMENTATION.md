# Documentação Técnica - Sistema Própolis do Frei

## Visão Geral
Este documento detalha a arquitetura técnica atual do sistema, focando nas recentes unificações de banco de dados, gestão de usuários e fluxos operacionais.

## 1. Arquitetura de Banco de Dados

### Unificação de Matrizes e Filiais
A distinção entre Matrizes e Filiais foi unificada em um único modelo, eliminando redundâncias e simplificando relacionamentos. O antigo modelo `Establishment` (e o app `apps.establishments`) foi **removido definitivamente** do código base.

*   **Model Principal:** `Distributor` (`apps/distributors/models.py`)
*   **Identificação Única:** O campo `id` utiliza `UUID` como chave primária, garantindo unicidade global.
*   **Tipagem de Unidade:** O campo `tipo_unidade` define a natureza da unidade:
    *   `MATRIZ`: Unidade central distribuidora.
    *   `FILIAL`: Unidade receptora de produtos.
    *   *Nota:* O campo `distributor_type` foi mantido para compatibilidade com legados, mas `tipo_unidade` é a referência atual.
*   **Código Identificador:** O campo `code` (ex: `DIST00001`) é gerado automaticamente e imutável, servindo como referência humanamente legível.
*   **Localização:** O campo `state` (UF) utiliza uma lista padronizada (`BRAZIL_STATES`) para garantir consistência de dados.

## 2. Gestão de Usuários

A gestão de acesso e permissões está intrinsecamente ligada à estrutura de Distribuidores.

*   **Vínculo com Unidade:** O modelo `User` (`apps/authentication/models.py`) possui um campo `distributor` (ForeignKey).
    *   Este campo vincula cada funcionário a uma única unidade de operação.
    *   **Regra de Negócio:** Todo usuário comum (não superusuário) **deve** estar vinculado a um distribuidor.
*   **Controle de Acesso:**
    *   O método `is_super_user_role()` determina se o usuário possui privilégios administrativos globais (geralmente associado a usuários sem vínculo restrito de distribuidor ou flag `is_superuser`).
    *   Nas views, o acesso aos dados (ex: pedidos, estoque) é filtrado automaticamente pelo `request.user.distributor`.

## 3. Fluxo de Pedidos (`/orders/`)

O módulo de pedidos gerencia a transferência de estoque entre a Matriz e as Filiais.

### Rotas Principais
*   **Listagem (`/orders/`):** Exibe pedidos filtrados pela unidade do usuário logado.
*   **Criação (`/orders/new/`):**
    *   **Origem:** Sempre uma unidade do tipo `MATRIZ` (selecionada no formulário).
    *   **Destino:** Automaticamente definido como o `distributor` do usuário logado (Filial solicitante).
    *   **Validação:** Impede a criação de pedidos com produtos inativos ou sem origem definida.
*   **Confirmação (`/orders/<uuid>/confirm/`):**
    *   Executa a baixa de estoque na Matriz (FIFO - *First In, First Out*).
    *   Registra a entrada de estoque na Filial.
    *   Gera registros de `StockMovement` para rastreabilidade completa (saída na origem, entrada no destino).

## 4. Padrões de Interface

O frontend do sistema segue padrões modernos para garantir responsividade e interatividade.

*   **Estilização:** Utiliza **Tailwind CSS** para design responsivo e consistente. As classes utilitárias (ex: `grid`, `flex`, `gap-4`, `card`) padronizam o layout de formulários e listagens.
*   **Interatividade:** Utiliza **HTMX** para interações dinâmicas sem recarregamento total da página (ex: filtros, atualizações parciais de listas).
*   **Configuração de Unidade:** As telas de "Configurar Unidade" (`distributor_form.html`) interagem diretamente com o model `Distributor`, garantindo que edições de cadastro (endereço, contato) reflitam imediatamente na única fonte de verdade do sistema.

## 5. Gerenciamento de Estoque

A integridade do estoque é mantida através de transações atômicas e um script de correção.

*   **Transações Atômicas**: Todas as operações que alteram o estoque (`registrar_entrada`, `registrar_saida`, `ajustar_estoque`) são envoltas em `@transaction.atomic`. Isso garante que a atualização do saldo (`ProductStock`) e a criação do registro de histórico (`StockMovement`) ocorram de forma indivisível, prevenindo dessincronizações.
*   **Correção de Saldo**: Em casos de inconsistência de dados, o script `recalculate_stock.py` pode ser executado para corrigir o saldo de um produto.
    *   **Execução**: `python manage.py runscript recalculate_stock`
    *   **Funcionamento**: O script recalcula o saldo de um produto com base em seu histórico de movimentações e atualiza o `ProductStock` com o valor correto.
*   **Estorno para Superusuários**: Superusuários têm a permissão de registrar saídas de estoque (estornos) mesmo que o saldo aparente ser insuficiente. Isso permite a correção manual de dados em situações emergenciais.

## 6. Padrões de Interface

Abaixo estão listados os pontos de atenção identificados para validação final:

*   **[ ] Teste Final de Criação de Pedido:** Validar o fluxo completo de "Novo Pedido" com diferentes perfis de usuário (Matriz vs Filial) para garantir que as restrições de origem/destino estão funcionando conforme esperado.
*   **[ ] Fluxo de Aprovação:** Implementar/Validar uma etapa explícita de aprovação pela Matriz antes da baixa de estoque (atualmente o fluxo permite confirmação direta se o usuário tiver permissão).
*   **[ ] Validação de Estoque:** Refinar as mensagens de erro caso a Matriz não possua estoque suficiente de um lote específico durante a confirmação.
