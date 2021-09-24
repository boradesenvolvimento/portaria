import datetime

from django.contrib.auth.models import User
from django.db import models
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
    garagem = models.CharField(max_length=5, choices=TIPO_GARAGEM)
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
        return self.id
