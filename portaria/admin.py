from django.contrib import admin
from .models import * #Cadastro, PaletControl, Motorista, Veiculos, ChecklistFrota, NfServicoPj, FuncPj, ManutencaoFrota


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
        ('notas', {'fields': ['notas']}),
        ('hr_chegada', {'fields':['hr_chegada']}),
        ('hr_saida',{'fields':['hr_saida']}),
        ('autor', {'fields': ['autor']}),
    ]
    list_display = ('id','placa', 'placa2', 'motorista', 'empresa','origem','destino','tipo_viagem','notas','tipo_mot','hr_chegada','hr_saida', 'autor')
admin.site.register(Cadastro, CadastroAdmin)

class PaleteControlAdmin(admin.ModelAdmin):
    pass
admin.site.register(PaleteControl, PaleteControlAdmin)

class MovPaleteAdmin(admin.ModelAdmin):
    pass
admin.site.register(MovPalete, MovPaleteAdmin)

class ClienteAdmin(admin.ModelAdmin):
    pass
admin.site.register(Cliente, ClienteAdmin)

class MotoristaAdmin(admin.ModelAdmin):
    pass
admin.site.register(Motorista, MotoristaAdmin)

class VeiculosAdmin(admin.ModelAdmin):
    pass
admin.site.register(Veiculos, VeiculosAdmin)

class ChecklistFrotaAdmin(admin.ModelAdmin):
    pass
admin.site.register(ChecklistFrota, ChecklistFrotaAdmin)

class NfServicoPjAdmin(admin.ModelAdmin):
    fieldsets = (
        ('funcionario',{'fields':['funcionario']}),
        ('faculdade', {'fields':['faculdade']}),
        ('cred_convenio', {'fields':['cred_convenio']}),
        ('outros_cred', {'fields':['outros_cred']}),
        ('desc_convenio', {'fields':['desc_convenio']}),
        ('outros_desc', {'fields': ['outros_desc']}),
        ('data_pagamento', {'fields': ['data_pagamento']}),
        ('data_emissao', {'fields':['data_emissao']}),
        ('autor', {'fields': ['autor']}),
    )
    list_display = ('funcionario', 'faculdade', 'cred_convenio', 'outros_cred', 'desc_convenio', 'outros_desc', 'data_emissao', 'autor')

admin.site.register(NfServicoPj, NfServicoPjAdmin)

class FuncPjAdmin(admin.ModelAdmin):
    pass
admin.site.register(FuncPj, FuncPjAdmin)

class MailsPJAdmin(admin.ModelAdmin):
    pass
admin.site.register(MailsPJ, MailsPJAdmin)

class ManutencaoFrotaAdmin(admin.ModelAdmin):
    pass
admin.site.register(ManutencaoFrota, ManutencaoFrotaAdmin)

class ServJoinManuAdmin(admin.ModelAdmin):
    pass
admin.site.register(ServJoinManu, ServJoinManuAdmin)

class CardFuncionarioAdmin(admin.ModelAdmin):
    pass
admin.site.register(CardFuncionario, CardFuncionarioAdmin)

class pj13Admin(admin.ModelAdmin):
    pass
admin.site.register(pj13, pj13Admin)

class feriaspjAdmin(admin.ModelAdmin):
    pass
admin.site.register(feriaspj, feriaspjAdmin)

class EmailMonitoramentoAdmin(admin.ModelAdmin):
    pass
admin.site.register(EmailMonitoramento, EmailMonitoramentoAdmin)

class TicketMonitoramentoAdmin(admin.ModelAdmin):
    pass
admin.site.register(TicketMonitoramento, TicketMonitoramentoAdmin)

class TicketChamadoAdmin(admin.ModelAdmin):
    pass
admin.site.register(TicketChamado,TicketChamadoAdmin)

class EmailChamadoAdmin(admin.ModelAdmin):
    pass
admin.site.register(EmailChamado,EmailChamadoAdmin)

class EmailOcorenciasMonitAdmin(admin.ModelAdmin):
    pass
admin.site.register(EmailOcorenciasMonit,EmailOcorenciasMonitAdmin)

class RomXMLAdmin(admin.ModelAdmin):
    pass
admin.site.register(RomXML,RomXMLAdmin)

class SkuRefXMLAdmin(admin.ModelAdmin):
    pass
admin.site.register(SkuRefXML,SkuRefXMLAdmin)

class EtiquetasDocumentoAdmin(admin.ModelAdmin):
    pass
admin.site.register(EtiquetasDocumento, EtiquetasDocumentoAdmin)

class BipagemEtiquetaAdmin(admin.ModelAdmin):
    pass
admin.site.register(BipagemEtiqueta, BipagemEtiquetaAdmin)

class RetornoEtiquetaAdmin(admin.ModelAdmin):
    pass
admin.site.register(RetornoEtiqueta,RetornoEtiquetaAdmin)


