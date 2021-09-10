from django.contrib import admin
from .models import Cadastro
# Register your models here.

class CadastroAdmin(admin.ModelAdmin):
    fieldsets = [
        ('placa', {'fields': ['placa']}),
        ('placa2', {'fields': ['placa2']}),
        ('motorista', {'fields': ['motorista']}),
        ('empresa',{'fields':['empresa']}),
        ('filial', {'fields':['filial']}),
        ('garagem', {'fields':['garagem']}),
        ('hr_chegada', {'fields':['hr_chegada']}),
        ('hr_saida',{'fields':['hr_saida']}),
        ('autor', {'fields': ['autor']}),
    ]
    list_display = ('placa', 'placa2', 'motorista', 'empresa','filial','garagem','hr_chegada','hr_saida', 'autor')

admin.site.register(Cadastro, CadastroAdmin)