from django.contrib import admin
from .models import Cadastro, PaletControl, Motorista, Veiculos, ChecklistFrota


# Register your models here.

class CadastroAdmin(admin.ModelAdmin):
    fieldsets = [
        ('placa', {'fields': ['placa']}),
        ('placa2', {'fields': ['placa2']}),
        ('motorista', {'fields': ['motorista']}),
        ('empresa',{'fields':['empresa']}),
        ('origem', {'fields':['origem']}),
        ('destino', {'fields': ['destino']}),
        ('tipo_mot', {'fields': ['tipo_mot']}),
        ('tipo_viagem', {'fields': ['tipo_viagem']}),
        ('hr_chegada', {'fields':['hr_chegada']}),
        ('hr_saida',{'fields':['hr_saida']}),
        ('autor', {'fields': ['autor']}),
    ]
    list_display = ('id','placa', 'placa2', 'motorista', 'empresa','origem','destino','tipo_viagem','tipo_mot','hr_chegada','hr_saida', 'autor')
admin.site.register(Cadastro, CadastroAdmin)

class PaletControlAdmin(admin.ModelAdmin):
    fieldsets = (
        ('loc_atual',{'fields':['loc_atual']}) ,
        ('ultima_viagem',{'fields':['ultima_viagem']}),
        ('origem',{'fields':['origem']}),
        ('destino',{'fields':['destino']}),
        ('placa_veic',{'fields':['placa_veic']})
    )
    list_display = ('id','loc_atual','ultima_viagem','origem','destino','placa_veic')
admin.site.register(PaletControl, PaletControlAdmin)

class MotoristaAdmin(admin.ModelAdmin):
    pass
admin.site.register(Motorista, MotoristaAdmin)

class VeiculosAdmin(admin.ModelAdmin):
    pass
admin.site.register(Veiculos, VeiculosAdmin)

class ChecklistFrotaAdmin(admin.ModelAdmin):
    pass
admin.site.register(ChecklistFrota, ChecklistFrotaAdmin)