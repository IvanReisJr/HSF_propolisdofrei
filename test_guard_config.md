# Django Test Guard - HSF_propolisdofrei
Este projeto utiliza uma arquitetura de Multi-unidade (Multitenancy).

## Regras de Ouro:
1. **Isolamento:** Nenhum QuerySet deve retornar dados de outra 'Unidade Distribuidora' para usuários que não sejam Superusuários.
2. **Custom User:** O modelo de usuário é o `CustomUser`. Nunca sugira o uso do `auth.User` padrão.
3. **Migrations:** Antes de sugerir novas migrations, verifique se campos obrigatórios possuem valores padrão (default) para não quebrar o banco atual.
4. **Imports:** Evite imports circulares entre `models.py` de diferentes apps.