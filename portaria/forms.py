from typing import Any, Dict, Mapping, Optional, Type, Union
from django import forms
from django.conf import settings
from django.core.files.base import File
from django.db.models import ImageField
from django.db.models.base import Model
from django.forms import Textarea, DateField
from django.forms.utils import ErrorList
from django_summernote.widgets import SummernoteWidget

from .models import Cadastro, TIPO_GARAGEM, ChecklistFrota, NfServicoPj, ManutencaoFrota, ServJoinManu, feriaspj, \
    FuncPj, Motorista, Veiculos, Cliente, PaleteControl, TipoServicosManut, RegistraTerceirizados, GARAGEM_CHOICES, \
        DisponibilidadeFrota, STATUS_FROTA_CHOICES, BonusPJ, ContratoPJ


#forms
class DateInput(forms.DateInput):
    input_type = 'date'


class isPlacaForm(forms.Form):
    search_placa = forms.CharField(max_length=20, label='Placa')
    search_dest = forms.ChoiceField(choices=TIPO_GARAGEM, label='Destino')
    kilometragem = forms.IntegerField()

class DateForm(forms.Form):
    date = forms.DateField(widget=DateInput(format=settings.DATE_FORMAT))
    date1 = forms.DateField(widget=DateInput(format=settings.DATE_FORMAT))


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
            'notas',
            'kilometragem',
            'hr_chegada',
            'hr_saida',
            'autor'
        ]


class DisponibilidadeFrotaForm(forms.ModelForm):
    class Meta:
        model = DisponibilidadeFrota
        fields = [
            'placa',
            'filial',
            'data_previsao',
            'observacao',
            'autor',
            'data_liberacao',
            'data_preenchimento',
            'ordem_servico',
            'status',
        ]
        widgets = {
            'data_preenchimento': DateInput(),
            'data_liberacao': DateInput(),
            'data_previsao': DateInput()
        }

class TPaletesForm(forms.Form):
    origem_ = forms.ChoiceField(
        choices=GARAGEM_CHOICES,
        required=True
    )
    destino_ = forms.ChoiceField(
        choices=GARAGEM_CHOICES,
        required=True
    )
    quantidade_ = forms.IntegerField()
    placa_veic = forms.CharField(max_length=7)
    tp_palete = forms.ChoiceField(choices=PaleteControl.TIPO_PALETE_CHOICES)
    motorista = forms.CharField(max_length=35)
    conferente = forms.CharField(max_length=35)

class FuncPjForm(forms.ModelForm):
    class Meta:
        model = FuncPj
        fields = [
            'filial',
            'nome',
            'cargo',
            'salario',
            'pix',
            'adiantamento',
            'ajuda_custo',
            'cpf_cnpj',
            'tipo_contrato',
            'banco',
            'ag',
            'conta',
            'op',
            'email',
            'ativo',
            'admissao'
        ]
        widgets = {
            'admissao': DateInput(),
        }

class MotoristaForm(forms.ModelForm):
    class Meta:
        model = Motorista
        fields = [
            'filial',
            'nome',
            'RG',
            'CPF',
            'telefone',
            'endereco',
            'bairro',
            'cidade',
            'UF',
            'cep',
            'data_nasc'
        ]
        widgets = {
            'data_nasc': DateInput(),
        }

class VeiculosForm(forms.ModelForm):
    class Meta:
        model = Veiculos
        fields = [
            'codigotpveic',
            'filial',
            'prefixoveic',
            'kmatualveic',
            'obsveic',
            'renavanveic',
            'modeloveic'
        ]

class ChecklistForm(forms.ModelForm):
    class Meta:
        model = ChecklistFrota
        fields = [
            'placacarreta',
            'placacarreta2',
            'kmatual',
            'horimetro',
            'filial',
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
            'p2_25',
            'p2_26',
            'p2_27',
            'p2_28',
            'p2_29',
            'p2_30',
            'p2_31',
            'p2_32',
            'p2_33',
            'p2_34',
            'obs_cavalo',
            'p3_1',
            'p3_2',
            'p3_3',
            'p3_4',
            'p3_5',
            'p3_6',
            'p3_7',
            'p3_8',
            'p3_9',
            'p3_10',
            'p3_11',
            'p3_12',
            'p3_13',
            'p3_14',
            'p3_15',
            'p3_16',
            'p3_17',
            'p3_18',
            'p3_19',
            'obs_carreta'
        ]
        widgets = {
            'obs_cavalo': Textarea(attrs={'cols': 30, 'rows': 3, 'style':'resize:none;'}),
            'obs_carreta': Textarea(attrs={'cols': 30, 'rows': 3, 'style':'resize:none;'}),
        }

class ServicoPjForm(forms.ModelForm):
    class Meta:
        model = NfServicoPj
        fields = [
            'faculdade',
            'cred_convenio',
            'outros_cred',
            'aux_moradia',
            'desc_convenio',
            'outros_desc',
            'data_pagamento'
        ]
        widgets = {
            'data_pagamento': DateInput(),
        }

class ManutencaoForm(forms.ModelForm):
    class Meta:
        model = ManutencaoFrota
        fields = [
            'socorro',
            'motorista',
            'tp_manutencao',
            'local_manu',
            'km_atual',
            'filial',
            'dt_ini_manu',
            'prev_entrega',
            'observacao',
        ]
        widgets = {
            'observacao': Textarea(attrs={'cols': 30, 'rows': 3, 'style':'resize:none;'}),
            'prev_entrega': DateInput(),
            'dt_ini_manu': DateInput(),
        }

class ServJoinManuForm(forms.ModelForm):
    class Meta:
        model = ServJoinManu
        fields = [
            'id_os',
            'id_svs'
        ]

class feriaspjForm(forms.ModelForm):
    class Meta:
        model = feriaspj
        fields = [
            'ultimas_ferias_ini',
            'ultimas_ferias_fim',
            'periodo',
            'quitado',
            'funcionario',
            'tp_pgto',
            'valor_integral',
            'valor_parcial1',
            'valor_parcial2',
            'observacao'
        ]
        widgets = {
            'ultimas_ferias_ini': DateInput(),
            'ultimas_ferias_fim': DateInput(),
        }

# class ClienteForm(forms.ModelForm):
#     class Meta:
#         model = Cliente
#         fields = [
#             'razao_social',
#             'cnpj',
#         ]

class BonusPJForm(forms.ModelForm):
    class Meta:
        model = BonusPJ
        fields = [
            'funcionario',
            'valor_pagamento',
            'data_pagamento',
            'observacao',
        ]
        widgets = {
            'data_pagamento': DateInput(),
        }
    def __init__(self, *args, **kwargs) -> None:
        super(BonusPJForm, self).__init__(*args, **kwargs)
        self.fields['observacao'].required = False

class ContratoPJForm(forms.ModelForm):
    anexo = forms.FileField()
    class Meta:
        model = ContratoPJ
        fields = [
            'funcionario',
            'inicio_contrato',
            'final_contrato',
            'data_reajuste',
            'valor_reajuste',
            'anexo',
            'observacao',
        ]
        widgets = {
            'inicio_contrato': DateInput(),
            'final_contrato': DateInput(),
            'data_reajuste': DateInput(),
        }
    
    def __init__(self, *args, **kwargs) -> None:
        super(ContratoPJForm, self).__init__(*args, **kwargs)
        self.fields['inicio_contrato'].required = False
        self.fields['final_contrato'].required = False
        self.fields['data_reajuste'].required = False
        self.fields['valor_reajuste'].required = False
        self.fields['anexo'].required = False
        self.fields['observacao'].required = False


class InsertTerceirizados(forms.ModelForm):
    class Meta:
        model = RegistraTerceirizados
        fields = [
            'fornecedor',
            'nome_funcionario',
            'rg',
            'cpf',
        ]

class UploadForm(forms.Form):
    file = forms.FileField(required=False,widget=forms.ClearableFileInput(attrs={'multiple': True}))

#summernote
class TextEditor(forms.Form):
    area = forms.CharField(widget=SummernoteWidget())

class SolicEstoque(forms.Form):
    filial = forms.CharField()
    extra_field_count = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        extra_fields = kwargs.pop('extra', 0)
        super(SolicEstoque, self).__init__(*args, **kwargs)
        self.fields['extra_field_count'].initial = extra_fields

        for index in range(int(extra_fields)):
            self.fields['item_{index}'.format(index=index)] = \
                forms.CharField()