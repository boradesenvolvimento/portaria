import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models
from django.db.models import SET_NULL
from django.utils import timezone

#validators
def only_int(value):
    try:
        int(value)
    except (ValueError,TypeError):
        raise ValidationError('NaN')


TIPO_MOT = (
    ('INTERNO', 'INTERNO'),
    ('AGREGADO', 'AGREGADO'),
)
TIPO_VIAGEM = (
    ('COLETA', 'COLETA'),
    ('ENTREGA', 'ENTREGA'),
    ('TRANSF', 'TRANSF')
)
TIPO_GARAGEM = (
    ('SPO','SPO'),
    ('REC','REC'),
    ('SSA','SSA'),
    ('FOR','FOR'),
    ('MCZ','MCZ'),
    ('NAT','NAT'),
    ('JPA','JPA'),
    ('AJU','AJU'),
    ('VDC','VDC'),
    ('MG','MG'),
    ('CTG','CTG'),
    ('TCO','TCO'),
    ('UDI','UDI'),
    ('TNA','TNA'),
    ('VIX','VIX'),
)
# Create your models here.
class Cadastro(models.Model):
    id = models.BigAutoField(primary_key=True)
    placa = models.CharField(max_length=7)
    placa2 = models.CharField(max_length=7, blank=True)
    motorista = models.CharField(max_length=50)
    empresa = models.CharField(max_length=30)
    origem = models.CharField(max_length=5, choices=TIPO_GARAGEM)
    destino = models.CharField(max_length=5, choices=TIPO_GARAGEM, blank=True, null=True)
    tipo_mot = models.CharField(max_length=10, choices=TIPO_MOT)
    tipo_viagem = models.CharField(max_length=10, choices=TIPO_VIAGEM)
    hr_chegada = models.DateTimeField(blank=True, default=timezone.now)
    hr_saida = models.DateTimeField(blank=True, null=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
       return self.placa

class PaletControl(models.Model):
    id = models.BigAutoField(primary_key=True)
    loc_atual = models.CharField(max_length=3, choices=TIPO_GARAGEM)
    ultima_viagem = models.DateField()
    origem = models.CharField(max_length=3,choices=TIPO_GARAGEM)
    destino = models.CharField(max_length=3, choices=TIPO_GARAGEM)
    placa_veic = models.CharField(max_length=7)

    class Meta:
        verbose_name = 'PaletControl'
        verbose_name_plural = 'PaletControl'

    def __int__(self):
        return str(self.id)

class Motorista(models.Model):
    codigomot = models.BigAutoField(primary_key=True)
    codigoveic = models.IntegerField()
    empresa = models.IntegerField(default=1)
    filial = models.IntegerField(default=1)
    nome = models.CharField(max_length=100)
    RG = models.CharField(max_length=20)
    CPF = models.CharField(max_length=11)
    telefone = models.IntegerField(max_length=11)
    endereco = models.CharField(max_length=100)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=20)
    UF = models.CharField(max_length=2)
    cep = models.IntegerField(max_length=8)
    data_nasc = models.DateField()

    def __str__(self):
       return self.nome

class Veiculos(models.Model):
    CODIGOTPVEIC_CHOICES = [
        ('1', 'VAN_PASSAGEIROS'),
        ('2', 'CAMINHAO'),
        ('3', 'CAVALO'),
        ('4', 'CARRETA'),
        ('5', 'VUC'),
        ('6', 'BITRUCK'),
        ('7', 'TOCO'),
        ('8', '3/4'),
        ('9', 'TRUCK'),
        ('10', 'VEICULO_APOIO'),
        ('11', 'PASSAGEIRO'),
        ('12', 'PASSAGEIRO_AUTOMOVEL')
    ]

    codigoveic = models.BigAutoField(primary_key=True)
    codigotpveic = models.CharField(max_length=5, choices=CODIGOTPVEIC_CHOICES)
    empresa = models.IntegerField(default=1)
    filial = models.IntegerField(default=1)
    garagem = models.IntegerField(default=1)
    prefixoveic = models.CharField(max_length=7)
    condicaoveic = models.CharField(max_length=20)
    capacidadetanqueveic = models.CharField(max_length=20)
    kmatualveic = models.IntegerField()
    obsveic = models.CharField(max_length=30)
    renavanveic = models.CharField(max_length=11)
    modeloveic = models.CharField(max_length=20)
    codmotorista = models.ForeignKey(Motorista, on_delete=SET_NULL, blank=True, null=True)

    def __str__(self):
       return self.prefixoveic

class ChecklistFrota(models.Model):
    idchecklist = models.BigAutoField(primary_key=True)
    datachecklist = models.DateField(default=timezone.now)
    placaveic = models.ForeignKey(Veiculos, on_delete=models.CASCADE)
    motoristaveic = models.ForeignKey(Motorista, on_delete=models.CASCADE)
    placacarreta = models.CharField(max_length=7, blank=True, null=True)
    kmanterior = models.IntegerField()
    kmatual = models.IntegerField()
    horimetro = models.CharField(max_length=10)
    p1_1 = models.BooleanField('Uniforme da Empresa')
    p1_2 = models.BooleanField('Motorista identificado por crachá')
    p2_1 = models.BooleanField('Lanterna do farol dianteiro funcionando?')
    p2_2 = models.BooleanField('Farol baixo funcionando?')
    p2_3 = models.BooleanField('Farol alto funcionando?')
    p2_4 = models.BooleanField('Lanterna direita funcionando?')
    p2_5 = models.BooleanField('Lanterna esquerda funcionando?')
    p2_6 = models.BooleanField('Lanternas traseiras funcionando?')
    p2_7 = models.BooleanField('Luz de ré funcionando?')
    p2_8 = models.BooleanField('Retrovisores estão em perfeito estado?')
    p2_9 = models.BooleanField('Água do radiador está no nível?')
    p2_10 = models.BooleanField('Óleo de freio está no nível?')
    p2_11 = models.BooleanField('Óleo de motor está no nível?')
    p2_12 = models.BooleanField('Verificado todas as luzes de advertências?')
    p2_13 = models.BooleanField('Verificado o freio de emergência?')
    p2_14 = models.BooleanField('Verificado o alarme sonoro da ré?')
    p2_15 = models.BooleanField('Verificado se existe vazamentos de óleo de motor?')
    p2_16 = models.BooleanField('Verificado se existe vazamento de ar?')
    p2_17 = models.BooleanField('Verificado se existe vazamento de óleo hidráulico?')
    p2_18 = models.BooleanField('Verificado se existe vazamento de água no radiador?')
    p2_19 = models.BooleanField('Verificado se as mangueiras estão em condições boas?')
    p2_20 = models.BooleanField('Pneus em boas condições?')
    p2_21 = models.BooleanField('As lonas de freio estão em boas condições?')
    p2_22 = models.BooleanField('Os estepes estão bons?')
    p2_23 = models.BooleanField('A suspensão está em condições perfeitas?')
    p2_24 = models.BooleanField('O carro está limpo e higienizado?')
    p3_1 = models.BooleanField('Foi verificado as luzes de advertência das laterais?')
    p3_2 = models.BooleanField('Foi verificado o lacre da placa?')
    p3_3 = models.BooleanField('Foi verificado se o aparelho thermoking apresenta falhas?')
    p3_4 = models.BooleanField('Foi verificado a carroceria, assoalho e baú?')
    p3_5 = models.BooleanField('Foi verificado a luz de freio?')
    p3_6 = models.BooleanField('Foi verificado a luz de ré?')
    p3_7 = models.BooleanField('Foi verificado se as luzes da lanterna traseira direita funciona?')
    p3_8 = models.BooleanField('Foi verificado se as luzes da lanterna traseira esquerda funciona?')
    teste = models.BooleanField('testando')

    def __str__(self):
       return str(self.idchecklist)

class FuncPj(models.Model):
    PESSOA_FISICA = 'PF'
    PESSOA_JURIDICA = 'PJ'
    TIPO_CONTRATO_CHOICES = [
        (PESSOA_FISICA, 'PF'),
        (PESSOA_JURIDICA, 'PJ'),
    ]

    id = models.BigAutoField(primary_key=True)
    filial = models.CharField(choices=TIPO_GARAGEM, max_length=3)
    nome = models.CharField(max_length=50)
    salario = models.IntegerField()
    cpf = models.CharField(max_length=11, validators=[only_int])
    cnpj = models.CharField(max_length=14, validators=[only_int])
    tipo_contrato = models.CharField(choices=TIPO_CONTRATO_CHOICES, max_length=2)
    banco = models.IntegerField()
    ag = models.IntegerField()
    conta = models.IntegerField()
    op = models.IntegerField()
    email = models.EmailField(max_length=254)
    ativo = models.BooleanField(default=True)

    def __str__(self):
       return self.nome

class NfServicoPj(models.Model):
    id = models.BigAutoField(primary_key=True)
    funcionario = models.ForeignKey(FuncPj, on_delete=models.CASCADE)
    premios_faculdade = models.IntegerField()
    ajuda_custo = models.IntegerField()
    adiantamento = models.IntegerField()
    convenio = models.IntegerField()
    outros_desc = models.IntegerField()
    data_emissao = models.DateField(default=timezone.now)

    def __str__(self):
       return str(self.id)
