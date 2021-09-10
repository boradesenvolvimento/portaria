from django import forms
from .models import Cadastro

#tuplas de escola
TIPO_PORTARIA = (
    ('1','ENTRADA'),
    ('2','SAIDA')
)

class isPlacaForm(forms.Form):
    search_placa = forms.CharField(max_length=20, label='search_placa')
    tipo_veic = forms.ChoiceField(choices=TIPO_PORTARIA, label='tipo_veic')

#inputs para pegar os dados
class CadastroForm(forms.ModelForm):
    class Meta:
        model = Cadastro
        fields = [
            'motorista',
            'empresa',
            'filial',
            'garagem',
            'hr_chegada',
            'hr_saida'
        ]
        readonly_fields = (
            'hr_chegada',
            'hr_saida'
        )





