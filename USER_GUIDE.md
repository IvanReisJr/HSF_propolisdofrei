# Guia de Usuário - Própolis do Frei

Bem-vindo ao sistema de gestão interna **Própolis do Frei**. Este guia explica como utilizar as principais funcionalidades do sistema.

## 1. Acesso ao Sistema
Acesse o sistema através da URL fornecida pelo administrador (ex: `http://localhost:8000`).
- Entre com seu **E-mail** e **Senha**.
- Se for seu primeiro acesso, solicite credenciais ao administrador.

---

## 2. Dashboard
A tela inicial exibe um resumo das operações:
- Total de produtos cadastrados.
- Alertas de estoque baixo.
- Pedidos pendentes de aprovação.

---

## 3. Gestão de Produtos
Acesse o menu **Produtos** para gerenciar o catálogo.

### Cadastrar Novo Produto
1. Clique em **Novo Produto**.
2. Preencha: Nome, Código (referência), Preço de Venda e Categoria.
3. Clique em **Salvar**.

### Unidades de Medida
O sistema suporta Múltiplas unidades (Unidade, Caixa, Litro). Configure-as no menu **Categorias/Unidades**.

---

## 4. Controle de Estoque
O estoque é separado por **Unidade de Negócio** (Matriz/Filial).

### Registrar Movimentação
Use esta função para dar entrada em notas fiscais, registrar perdas ou transferências manuais.
1. Vá em **Estoque > Nova Movimentação**.
2. O sistema selecionará automaticamente sua **Unidade** (Distribuidor vinculado).
2. Selecione o **Produto**.
3. Escolha o **Tipo**:
   - *Entrada Manual*: Nota fiscal ou compra.
   - *Saída Manual*: Uso interno ou perda.
   - *Ajuste*: Correção de inventário.
4. Informe a quantidade. O sistema mostrará o **Saldo Atual** para ajudar.
5. Adicione uma justificativa e salve.

---

## 5. Pedidos de Distribuição
Use este módulo para enviar mercadorias de uma Unidade Central para Distribuidores ou outras Filiais.

### Criar Pedido
1. Vá em **Pedidos > Novo Pedido**.
2. Selecione o **Distribuidor** (Destino).
3. Selecione a **Unidade de Origem** (de onde sai a mercadoria).
4. Adicione produtos na lista.
5. **Preço**: O sistema sugere o preço de tabela, mas você pode editar se houver negociação especial.
6. Clique em **Salvar Rascunho**.

### Confirmar Pedido
Um pedido criado fica como *Pendente*.
1. Abra o pedido.
2. Revise os itens e valores.
3. Clique em **Confirmar Pedido**.
   - ⚠️ Isso irá **baixar o estoque** da Unidade de Origem automaticamente.

---

## 6. Auditoria (Logs)
O sistema grava todas as ações importantes (quem criou, quem editou, quem excluiu).
- Acesse **Configurações > Auditoria** para ver o histórico.
