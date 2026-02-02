# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não Lançado]

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
  - "Distribuições Recentes" limitada a exibir os 3 primeiros itens
  - Divider cartões "Inventário Rápido" e "Relatórios" em linha 50/50 na coluna da direita
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
