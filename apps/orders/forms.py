from django import forms
from .models import AccountSettlement
from django.utils.translation import gettext_lazy as _
import os

class SettlementUploadForm(forms.ModelForm):
    class Meta:
        model = AccountSettlement
        fields = ['value_reported', 'receipt_file']
        widgets = {
            'value_reported': forms.NumberInput(attrs={'class': 'form-control block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50', 'step': '0.01'}),
            'receipt_file': forms.FileInput(attrs={'class': 'form-control block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary hover:file:bg-primary-100'}),
        }

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)

    def clean_value_reported(self):
        value = self.cleaned_data.get('value_reported')
        if value and self.order:
            # Calcular saldo pendente (excluindo o valor que está sendo enviado agora)
            # Como pending_balance já desconta tudo o que foi submetido, precisamos garantir que o novo valor não exceda
            # o que realmente falta.
            # O pending_balance atual no banco reflete (Total - Já Submetidos).
            # O usuário está tentando submeter 'value'.
            # Logo, value não pode ser maior que pending_balance.
            if value > self.order.pending_balance:
                 raise forms.ValidationError(
                    _('O valor informado (R$ %(value)s) excede o saldo devedor (R$ %(balance)s).'),
                    params={'value': value, 'balance': self.order.pending_balance}
                )
        return value

    def clean_receipt_file(self):
        receipt = self.cleaned_data.get('receipt_file')
        if receipt:
            ext = os.path.splitext(receipt.name)[1].lower()
            valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            if ext not in valid_extensions:
                raise forms.ValidationError(_('Extensão não permitida. Use: .pdf, .jpg, .jpeg, .png'))
        return receipt
