# Sistema de Gestão Própolis do Frei 🐝

Sistema de gestão interna para controle de produtos, estoque e distribuição (pedidos), desenvolvido como um **Monolito Django** robusto focado em performance, simplicidade e facilidade de manutenção.

## 🚀 Visão Geral

Este projeto substitui soluções anteriores por uma arquitetura centralizada em Python/Django, eliminando a complexidade de SPAs (React/Vue) desnecessários para este caso de uso. A interatividade é garantida via **HTMX**, proporcionando uma experiência fluida sem a sobrecarga de um framework JavaScript pesado.

### Principais Funcionalidades
- **Gestão de Produtos**: Cadastro de produtos, categorias e unidades.
- **Controle de Estoque**: Registro de entradas, saídas e ajustes com validação em tempo real.
- **Pedidos de Distribuição**:
  - Criação de pedidos para distribuidores/filiais.
  - Seleção de unidade de origem.
  - Edição manual de preços (negociação).
  - Atualização automática de estoque ao confirmar.
- **Multi-Unidade**: Suporte para múltiplas unidades (filiais) com isolamento de dados por usuário.
- **Auditoria**: Logs detalhados de todas as ações críticas.

---

## 🛠️ Tecnologias

- **Backend**: Python 3.12+, Django 5.x
- **Frontend**: Django Templates + HTMX (para interatividade)
- **CSS**: Tailwind CSS (via CDN ou build process simplificado)
- **Banco de Dados**: SQLite (Desenvolvimento) / PostgreSQL (Produção - recomendado)
- **Ícones**: Lucide Icons

---

## ⚡ Como Rodar o Projeto

### Pré-requisitos
- Python 3.12 ou superior instalado.

### Passo a Passo

1. **Clone o repositório**
   ```bash
   git clone <URL_DO_REPO>
   cd propolisdofrei
   ```

2. **Crie e ative o ambiente virtual**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Prepare o Banco de Dados**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Crie um Superusuário**
   ```bash
   python manage.py createsuperuser
   ```

6. **Rode o Servidor**
   ```bash
   python manage.py runserver
   ```
   Acesse: `http://127.0.0.1:8000/`

---

## 📂 Estrutura do Projeto

```
propolisdofrei/
├── apps/                 # Aplicações Django (Módulos)
│   ├── authentication/   # Usuários e Login
│   ├── core/             # Views globais e dashboard
│   ├── products/         # Modelos de produtos e categorias
│   ├── stock/            # Movimentações de estoque
│   ├── orders/           # Pedidos de distribuição
│   ├── distributors/     # Gestão de parceiros e unidades (Matriz/Filiais)
│   └── establishments/   # [LEGADO] Antiga gestão de unidades
├── templates/            # Arquivos HTML (Django Templates)
├── static/               # CSS, Imagens, JS
└── config/               # Configurações do projeto (settings.py)
```

## 📖 Documentação Adicional

- [Arquitetura e Decisões Técnicas](ARCHITECTURE.md)
- [Guia de Uso](USER_GUIDE.md)
- [Guia de Reutilização para Desenvolvedores](reuse_guide.md)

---

**Desenvolvido com ❤️ pela equipe Própolis do Frei.**
