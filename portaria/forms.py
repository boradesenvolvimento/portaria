from django import forms


from .models import Cadastro, TIPO_GARAGEM


#tuplas de escolha

#forms
class DateInput(forms.DateInput):
    input_type = 'date'

class isPlacaForm(forms.Form):
    search_placa = forms.CharField(max_length=20, label='search_placa')

class DateForm(forms.Form):
    date = forms.CharField(max_length=10)
    date1 = forms.CharField(max_length=10)

class FilterForm(forms.Form):
    filter_ = forms.CharField(max_length=30)

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

class TPaletsForm(forms.Form):
    origem_ = forms.ChoiceField(choices=TIPO_GARAGEM)
    destino_ = forms.ChoiceField(choices=TIPO_GARAGEM)
    quantidade_ = forms.IntegerField()
    placa_veic = forms.CharField(max_length=7)





