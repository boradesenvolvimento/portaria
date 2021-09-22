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
    ('SPO','1'),
    ('REC','2'),
    ('SSA','3'),
    ('FOR','4'),
    ('MCZ','5'),
    ('NAT','6'),
    ('JPA','7'),
    ('AJU','8'),
    ('VDC','9'),
    ('MG','10'),
    ('CTG','20'),
    ('TCO','21'),
    ('UDI','22'),
    ('TNA','23'),
    ('VIX','24'),
)
# Create your models here.
class Cadastro(models.Model):
    id = models.BigAutoField(primary_key=True)
    placa = models.CharField(max_length=7)
    placa2 = models.CharField(max_length=7, blank=True)
    motorista = models.CharField(max_length=50)
    empresa = models.CharField(max_length=30)
    garagem = models.CharField(max_length=5, choices=TIPO_GARAGEM)
    tipo_func = models.CharField(max_length=10, choices=TIPO_MOT)
    tipo_viagem = models.CharField(max_length=10, choices=TIPO_VIAGEM)
    hr_chegada = models.DateTimeField(blank=True, default=timezone.now)
    hr_saida = models.DateTimeField(blank=True, null=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
       return self.placa


