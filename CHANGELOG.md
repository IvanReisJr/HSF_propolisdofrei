# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não Lançado]

### 2026-02-05 (Fase 02 - Blindagem & Estoque)

#### Adicionado
- **Segurança & Blindagem**:
  - Implementado Isolamento Lógico (Multi-tenancy) por `Distributor` em Embalagens e Estoque.
  - Signal `user_logged_in` para bloquear acesso de usuários vinculados a distribuidores inativos.
- **Inativação (Soft Delete)**:
  - Adicionado campo `is_active` e lógica de inativação para `UnitOfMeasure`, `Category` e `Distributor`.
  - Views de inativação com verificação de permissão (`is_staff` para Unidades, `is_superuser` para Distribuidores).
- **Estoque**:
  - View `registrar_entrada` com transação atômica (`transaction.atomic`) e filtro por Distribuidor.
  - Modelos `ProductStock` e `StockMovement` atualizados para usar `Distributor` em vez de Establishment.
- **Torre de Controle**:
  - View `dashboard_matriz_consolidado` com agregação de saldos por filial (Acesso restrito à Matriz).
- **Hierarquia e Fluxo**:
  - Modelo `Distributor`: Campo `tipo_unidade` (MATRIZ/FILIAL).
  - Decorator `matriz_required`: Restrição de cadastros globais à Matriz.
  - Sidebar Dinâmica: Menu 'Cadastros' oculto para Filiais.
  - Pedido Multi-CD: Filial escolhe CD de Origem (Matriz) e é fixada como Destino.

#### Alterado
- **Documentação**: Atualizado `documentacao_projeto_hsf_V2.txt` com a Seção 5 (Blindagem e Segurança).
- **Modelo de Pedido**: Suporte a Origem/Destino (Campos `target_distributor` e redefinição de `distributor`).

### 2026-02-03 (Fase 01 - DB Reset & Escopo)

#### Adicionado
- Funcionalidade de **Embalagem** (Packaging):
  - Criado modelo `Packaging` e tabela `packagings`.
  - Adicionado campo `packaging` ao modelo `Product`.
  - Interface Admin para gerenciar Tipos de Embalagem.
  - Dropdown de Embalagem no formulário de Crição/Edição de Produto.
  - Exibição da Embalagem na tela de Detalhes do Produto.
- `CustomUserAdmin` atualizado com `add_fieldsets` para permitir cadastro de Usuário com Distribuidor via Admin.
- **Interface de Gestão de Embalagens** no projeto (fora do Admin):
  - Páginas para Listar, Criar e Editar embalagens (`/products/packagings/`).
  - Link "Embalagens" adicionado ao menu "Cadastros" na sidebar.

#### Alterado
- **Reset de Banco de Dados**: Base zerada para início da "Fase 01".
- **Escopo de Usuário**:
  - `User` agora **exige** vínculo com `Distributor` (exceto superusuários).
  - Removido/Depreciado uso direto de `establishment` no modelo de `User`.
- **Dashboard**:
  - Atualizado para exibir Nome do Distribuidor (`user.distributor.name`) em vez de Estabelecimento.
  - Estatísticas de Estoque/Pedidos desativadas temporariamente (aguardando refatoração de Estoque Fase 02).

#### Corrigido
- Erro `AttributeError: 'User' object has no attribute 'establishment'` em views e templates.
- Erro `UserForm has no field named 'distributor'` ao criar usuário via Admin.

### 2026-02-02

#### Adicionado
- Filtros funcionais nas abas de status da lista de pedidos (Todos, Pendentes, Confirmados, Cancelados)
- Scroll responsivo na tabela de "Distribuições Recentes" do Dashboard (altura: 240px, ~3 linhas)
- Geração automática de `order_number` no modelo `Order` para evitar conflitos de constraint única

#### Corrigido
- Tags Django quebradas no Dashboard:
  - `{{ user.establishment.name|default:"Geral" }}`
  - `{{ stats.pending_orders|default:"0" }}`
  - `{{ order.order_number }}`
- Tags Django quebradas em `order_detail.html`:
  - `{{ order.get_status_display }}`
  - `{{ order.distributor.state }}`
  - `{{ order.total_amount }}`
- Botão "Adicionar Item" no formulário de novo pedido (corrigido ID duplicado)
- Cálculo do "Valor Total Estimado" no formulário de pedidos
- Máscara de entrada para "Preço Unitário" (formato monetário brasileiro)

#### Alterado
- Layout do Dashboard:
  - Texto do hero consolidado em uma única linha (max-width: 700px)
  - Padding de todos os cartões reduzido de `p-4` para `p-3`
  - Gap entre cartões de ação reduzido de `gap-4` para `gap-2`
  - Altura da tabela de distribuições alterada de `40vh` para `240px`
  - Reestruturação de layout: "Distribuições Recentes" e Cards de Ação lado a lado (2 colunas)
  - "Distribuições Recentes" limitada a 5 itens visíveis (com scroll para até 50) e altura ajustada para 400px
  - "Distribuições Recentes" estritamente limitada a 3 itens (sem scroll)
  - Lista de "Produtos" limitada a 4 linhas visíveis (320px) com cabeçalho fixo e scroll
  - Lista de "Pedidos de Distribuição" limitada a 5 linhas visíveis (400px) com cabeçalho fixo e scroll
  - Divider cartões "Inventário Rápido" e "Relatórios" em linha 50/50 na coluna da direita
  - Ajuste global de layout: `app-container` com altura fixa (100vh) para evitar corte de conteúdo e habilitar scroll interno correto
- Filtros de status na lista de pedidos agora usam query parameters (`?status=...`)
- Estilo visual das abas ativas nos filtros (cor primária + borda inferior)

#### Técnico
- Implementado método `save()` customizado no modelo `Order` para auto-geração de números únicos
- Formato de número de pedido: `PED-YYYYMMDD-NNNN` (ex: PED-20260202-0001)
- Adicionado parâmetro `status_filter` na view `order_list` para filtrar pedidos
- Context atualizado em `order_list` para passar filtro ativo ao template

---

## Formato de Entrada

Para manter este changelog atualizado, use o seguinte formato:

```markdown
### YYYY-MM-DD

#### Adicionado
- Novas funcionalidades

#### Corrigido
- Bugs corrigidos

#### Alterado
- Mudanças em funcionalidades existentes

#### Removido
- Funcionalidades removidas

#### Técnico
- Detalhes técnicos de implementação
```
