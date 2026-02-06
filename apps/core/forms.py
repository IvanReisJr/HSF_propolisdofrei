from django import forms

class ReadOnlyPKMixin:
    """
    Mixin para tornar campos de identificação (PK/Código) somente leitura
    durante a edição (quando a instância já existe).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Lista de campos que geralmente são identificadores
            # Adapte conforme os nomes reais dos seus campos
            pk_fields = ['code', 'codigo', 'username', 'email', 'cnpj', 'document']
            
            for field_name in pk_fields:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs['readonly'] = True
                    self.fields[field_name].disabled = True
                    self.fields[field_name].help_text = 'Identificação não pode ser alterada após a criação.'

class BaseForm(ReadOnlyPKMixin, forms.ModelForm):
    """
    Classe base para formulários do sistema herdarem.
    """
    pass
