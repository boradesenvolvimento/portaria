import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone



# Create your models here.
class Cadastro(models.Model):
    placa = models.CharField(max_length=20, primary_key=True)
    placa2 = models.CharField(max_length=20, blank=True)
    motorista = models.CharField(max_length=50)
    empresa = models.IntegerField()
    filial = models.IntegerField()
    garagem = models.IntegerField()
    hr_chegada = models.DateTimeField(blank=True)
    hr_saida = models.DateTimeField(blank=True, null=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
       return self.placa


