from django import forms


from .models import Cadastro, TIPO_GARAGEM, ChecklistFrota, NfServicoPj

#forms
class DateInput(forms.DateInput):
    input_type = 'date'

class isPlacaForm(forms.Form):
    search_placa = forms.CharField(max_length=20, label='Placa')
    search_dest = forms.ChoiceField(choices=TIPO_GARAGEM, label='Destino')

class DateForm(forms.Form):
    date = forms.DateField()
    date1 = forms.DateField()

class FilterForm(forms.Form):
    filter_ = forms.CharField(max_length=30, label='')

#inputs para pegar os dados
class CadastroForm(forms.ModelForm):
    class Meta:
        model = Cadastro
        fields = [
            'placa',
            'placa2',
            'motorista',
            'empresa',
            'origem',
            'destino',
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

class ChecklistForm(forms.ModelForm):
    class Meta:
        model = ChecklistFrota
        fields = [
            'placacarreta',
            'kmanterior',
            'kmatual',
            'horimetro',
            'p1_1',
            'p1_2',
            'p2_1',
            'p2_2',
            'p2_3',
            'p2_4',
            'p2_5',
            'p2_6',
            'p2_7',
            'p2_8',
            'p2_9',
            'p2_10',
            'p2_11',
            'p2_12',
            'p2_13',
            'p2_14',
            'p2_15',
            'p2_16',
            'p2_17',
            'p2_18',
            'p2_19',
            'p2_20',
            'p2_21',
            'p2_22',
            'p2_23',
            'p2_24',
            'p3_1',
            'p3_2',
            'p3_3',
            'p3_4',
            'p3_5',
            'p3_6',
            'p3_7',
            'p3_8'
        ]




class ServicoPjForm(forms.ModelForm):
    class Meta:
        model = NfServicoPj
        fields = [
            'premios_faculdade',
            'ajuda_custo',
            'adiantamento',
            'convenio',
            'outros_desc',
            'data_emissao'
        ]
