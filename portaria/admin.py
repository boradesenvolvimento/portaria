from django.contrib import admin
from .models import Cadastro
# Register your models here.

class CadastroAdmin(admin.ModelAdmin):
    fieldsets = [
        ('placa', {'fields': ['placa']}),
        ('placa2', {'fields': ['placa2']}),
        ('motorista', {'fields': ['motorista']}),
        ('empresa',{'fields':['empresa']}),
        ('garagem', {'fields':['garagem']}),
        ('tipo_func', {'fields': ['tipo_func']}),
        ('tipo_viagem', {'fields': ['tipo_viagem']}),
        ('hr_chegada', {'fields':['hr_chegada']}),
        ('hr_saida',{'fields':['hr_saida']}),
        ('autor', {'fields': ['autor']}),
    ]
    list_display = ('id','placa', 'placa2', 'motorista', 'empresa','garagem','tipo_viagem','tipo_func','hr_chegada','hr_saida', 'autor')

admin.site.register(Cadastro, CadastroAdmin)