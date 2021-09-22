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
    ('1','SPO'),
    ('2','REC'),
    ('3','SSA'),
    ('4','FOR'),
    ('5','MCZ'),
    ('6','NAT'),
    ('7','JPA'),
    ('8','AJU'),
    ('9','VDC'),
    ('10','MG'),
    ('20','CTG'),
    ('21','TCO'),
    ('22','UDI'),
    ('23','TNA'),
    ('24','VIX'),
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


