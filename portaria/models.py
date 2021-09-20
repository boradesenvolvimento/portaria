import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

TIPO_FUNC = (
    ('INTERNO', 'INTERNO'),
    ('AGREGADO', 'AGREGADO'),
)
TIPO_VIAGEM = (
    ('COLETA', 'COLETA'),
    ('ENTREGA', 'ENTREGA'),
    ('TRANSF', 'TRANSF')
)
# Create your models here.
class Cadastro(models.Model):
    id = models.BigAutoField(primary_key=True)
    placa = models.CharField(max_length=7)
    placa2 = models.CharField(max_length=20, blank=True)
    motorista = models.CharField(max_length=50)
    empresa = models.CharField(max_length=100)
    garagem = models.IntegerField()
    tipo_func = models.CharField(max_length=10, choices=TIPO_FUNC)
    tipo_viagem = models.CharField(max_length=10, choices=TIPO_VIAGEM)
    hr_chegada = models.DateTimeField(blank=True, default=timezone.now)
    hr_saida = models.DateTimeField(blank=True, null=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
       return self.placa


