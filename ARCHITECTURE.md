# Arquitetura do Sistema Própolis do Frei

Este documento descreve as decisões arquiteturais, padrões de código e estrutura do sistema.

## 1. Visão Geral da Arquitetura

O sistema segue o padrão **Django Monolith** (Monolito Modular). Ao contrário de arquiteturas separadas (Frontend SPA + Backend API), optamos pelo acoplamento forte para ganhar:
- **Velocidade de Desenvolvimento**: Sem duplicação de modelos/tipos entre front e back.
- **Simplicidade**: Uma única codebase, um único deploy.
- **Performance**: Renderização no servidor (SSR) é rápida e eficiente para dashboards administrativos.

### Tech Stack
- **Backend Framework**: Django 5.x
- **Database**: SQLite (Dev) / PostgreSQL (Prod)
- **Frontend**: Django Templates (HTML renderizado no servidor)
- **Interatividade**: HTMX (para requisições AJAX declarativas sem escrever JS complexo)
- **Estilização**: Tailwind CSS (Utility-first)

---

## 2. Organização dos Módulos (Apps)

O projeto está dividido em aplicações pequenas e focadas dentro da pasta `apps/`:

| App | Responsabilidade | Models Principais |
|-----|------------------|-------------------|
| `authentication` | Gestão de usuários e login customizado | `User` (AbstractUser) |
| `products` | Catálogo, Categorias e Unidades de Medida | `Product`, `Category`, `ProductStock` |
| `stock` | Movimentações (Entrada/Saída) e Auditoria | `StockMovement` |
| `orders` | Pedidos de distribuição entre unidades | `Order`, `OrderItem` |
| `distributors` | Unidades de Negócio (Matriz, Filiais e Parceiros) | `Distributor` |
| `core` | Utilitários globais, Dashboard e Middlewares | - |

---

## 3. Padrões de Frontend

### HTMX vs JavaScript Puro
- **HTMX**: Usado para interações que buscam dados do servidor (ex: buscar saldo de estoque ao selecionar produto, paginação infinita, filtros de tabela).
- **JavaScript (Vanilla)**: Usado apenas para interações puramente locais (ex: fechar modal, máscara de moeda, alternar abas).

### ⚠️ Regra Crítica: Templates e Formatadores
Devido a problemas com formatadores automáticos de HTML em certos ambientes, adotamos o padrão **Vertical Block** para tags Django propensas a erro, especialmente dentro de tags HTML.

**❌ NÃO FAÇA ( risco de quebra de sintaxe):**
```html
<option value="1" {% if x == y %}selected{% endif %}>Opção</option>
```

**✅ FAÇA (Padrão Vertical):**
```html
{% if x == y %}
    <option value="1" selected>Opção</option>
{% else %}
    <option value="1">Opção</option>
{% endif %}
```
Isso garante que o parser do Django nunca receba algo como `x==y` (sem espaços) ou tags quebradas.

---

## 4. Fluxos Críticos

### Ciclo de Vida do Pedido
1. **Criação (Pendente)**: Usuário seleciona Unidade de Origem, Distribuidor e Itens. O estoque NÃO é baixado ainda.
2. **Confirmação**:
   - Sistema verifica saldo atual em `ProductStock`.
   - Deduz quantidade (`current_stock -= qty`).
   - Gera registro em `StockMovement` (tipo: 'exit').
   - Muda status do pedido para `Confirmado`.
3. Cancelamento: Apenas pedidos `Pendentes` podem ser cancelados. Não afeta estoque.

---

## 5. Fase 02: Blindagem e Multi-Tenancy (Fev/2026)

Implementamos um isolamento lógico robusto para garantir que usuários de uma filial não acessem dados de outra.

### 5.1. Isolamento de Dados
- **Distributor como Entidade Central**: `ProductStock`, `StockMovement`, `Order` e `Packaging` agora são vinculados diretamente a `Distributor`.
- **Regra de Ouro**: Filtros globais garantem que usuários comuns só vejam registros onde `distributor = request.user.distributor`.
- **Establishment Removido**: O antigo modelo `Establishment` foi removido definitivamente do código base, sendo substituído integralmente por `Distributor`.

### 5.2. Segurança e Controle
- **Inativação Segura (Soft Delete)**: `is_active` em vez de `delete()` físico para modelos críticos (`Product`, `Category`, `Distributor`).
- **Torre de Controle (Matriz)**: Novo Dashboard Consolidado permite à Matriz visualizar estoques globais, enquanto Filiais veem apenas o local.
- **Login Guard**: Signal `user_logged_in` impede acesso se o Distribuidor vinculado estiver inativo.

---

## 6. Deployment

O sistema está preparado para deploy via Docker ou paaS (como Railway/Render).
- **Static Files**: Configuradon via `whitenoise`.
- **Database**: Configurado via `dj-database-url` para ler `DATABASE_URL` do ambiente.
