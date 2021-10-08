import datetime

from django.contrib.auth.models import User
from django.core.validators import MaxLengthValidator
from django.db import models
from django.db.models import SET_NULL
from django.utils import timezone

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
    SN_CHOICES = [
        ('S','S'),
        ('N', 'N'),
    ]

    idchecklist = models.BigAutoField(primary_key=True)
    datachecklist = models.DateField(default=timezone.now)
    placaveic = models.ForeignKey(Veiculos, on_delete=models.CASCADE)
    motoristaveic = models.ForeignKey(Motorista, on_delete=models.CASCADE)
    placacarreta = models.CharField(max_length=7, blank=True, null=True)
    kmanterior = models.IntegerField()
    kmatual = models.IntegerField()
    horimetro = models.CharField(max_length=10)
    p1_1 = models.CharField(max_length=1, choices=SN_CHOICES)
    p1_2 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_1 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_2 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_3 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_4 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_5 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_6 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_7 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_8 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_9 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_10 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_11 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_12 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_13 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_14 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_15 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_16 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_17 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_18 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_19 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_20 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_21 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_22 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_23 = models.CharField(max_length=1, choices=SN_CHOICES)
    p2_24 = models.CharField(max_length=1, choices=SN_CHOICES)
    p3_1 = models.CharField(max_length=1, choices=SN_CHOICES)
    p3_2 = models.CharField(max_length=1, choices=SN_CHOICES)
    p3_3 = models.CharField(max_length=1, choices=SN_CHOICES)
    p3_4 = models.CharField(max_length=1, choices=SN_CHOICES)
    p3_5 = models.CharField(max_length=1, choices=SN_CHOICES)
    p3_6 = models.CharField(max_length=1, choices=SN_CHOICES)
    p3_7 = models.CharField(max_length=1, choices=SN_CHOICES)
    p3_8 = models.CharField(max_length=1, choices=SN_CHOICES)

    def __str__(self):
       return str(self.idchecklist)

class FuncPj(models.Model):
    id = models.BigAutoField(primary_key=True)
    unidade = models.CharField(max_length=30)
    nome = models.CharField(max_length=50)
    salario = models.IntegerField()
    cpf_cnpj = models.IntegerField()
    banco = models.IntegerField()
    ag = models.IntegerField()
    conta = models.IntegerField()
    op = models.IntegerField()
    email = models.EmailField(max_length=254)

    def __str__(self):
       return self.nome

class NfServicoPj(models.Model):
    id = models.BigAutoField(primary_key=True)
    funcionario = models.ForeignKey(FuncPj, on_delete=models.CASCADE)
    premios_faculdade = models.IntegerField()
    ajuda_custo = models.IntegerField()
    adiantamento = models.IntegerField()
    convenio = models.IntegerField()
    data_emissao = models.DateField(default=timezone.now)

    def __str__(self):
       return str(self.id)
