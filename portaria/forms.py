from django import forms


from .models import Cadastro

#tuplas de escolha

#forms
class DateInput(forms.DateInput):
    input_type = 'date'

class isPlacaForm(forms.Form):
    search_placa = forms.CharField(max_length=20, label='search_placa')

class DateForm(forms.Form):
    date = forms.CharField(max_length=10)
    date1 = forms.CharField(max_length=10)

#inputs para pegar os dados
class CadastroForm(forms.ModelForm):
    class Meta:
        model = Cadastro
        fields = [
            'placa',
            'placa2',
            'motorista',
            'empresa',
            'garagem',
            'tipo_mot',
            'tipo_viagem',
            'hr_chegada',
            'hr_saida',
            'autor'
        ]






