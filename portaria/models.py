import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, DecimalValidator
from django.db import models
from django.db.models import PROTECT, Sum, F
from django.utils import timezone



#validators


def only_int(value):
    try:
        int(value)
    except (ValueError,TypeError):
        raise ValidationError('Valor digitado não é um número')


TIPO_MOT = (
    ('INTERNO', 'INTERNO'),
    ('AGREGADO', 'AGREGADO'),
    ('SEM_VINCULO', 'SEM_VINCULO'),
)
TIPO_VIAGEM = (
    ('COLETA', 'COLETA'),
    ('ENTREGA', 'ENTREGA'),
    ('TRANSF', 'TRANSF'),
    ('NENHUM', 'NENHUM')
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
TIPO_DOCTO_CHOICES = (
    ('8', 'NFS'),
    ('57', 'CTE')
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
    tipo_mot = models.CharField(max_length=11, choices=TIPO_MOT)
    tipo_viagem = models.CharField(max_length=10, choices=TIPO_VIAGEM)
    hr_chegada = models.DateTimeField(blank=True)
    hr_saida = models.DateTimeField(blank=True, null=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        verbose_name = 'Cadastro'
        verbose_name_plural = 'Cadastro'

    def __str__(self):
       return self.placa

class PaleteControl(models.Model):
    TIPO_PALETE_CHOICES = [
        ('CHEP', 'CHEP'),
        ('PBR','PBR')
    ]
    id = models.BigAutoField(primary_key=True)
    loc_atual = models.CharField(max_length=3, choices=TIPO_GARAGEM)
    tp_palete = models.CharField(max_length=4, choices=TIPO_PALETE_CHOICES)
    autor = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'PaleteControl'
        verbose_name_plural = 'PaleteControl'

    def __str__(self):
        return str(self.id)

class MovPalete(models.Model):
    id = models.BigAutoField(primary_key=True)
    palete = models.ForeignKey(PaleteControl, on_delete=PROTECT)
    data_ult_mov = models.DateField(default=timezone.now)
    origem = models.CharField(max_length=3, choices=TIPO_GARAGEM)
    destino = models.CharField(max_length=3, choices=TIPO_GARAGEM)
    placa_veic = models.CharField(max_length=7)
    autor = models.ForeignKey(User, on_delete=PROTECT)

    def __str__(self):
        return str(self.id)

class Cliente(models.Model):
    TP_VINCULO = [
        ('INTERNO','INTERNO'),
        ('CLIENTE','CLIENTE')
    ]
    id = models.BigAutoField(primary_key=True)
    razao_social = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=14, validators=[only_int])
    intex = models.CharField(max_length=7, choices=TP_VINCULO)
    saldo = models.IntegerField()

    def __str__(self):
        return self.razao_social

class Motorista(models.Model):
    codigomot = models.BigAutoField(primary_key=True)
    filial = models.CharField(max_length=3, choices=TIPO_GARAGEM)
    nome = models.CharField(max_length=100)
    RG = models.CharField(max_length=20, validators=[only_int])
    CPF = models.CharField(max_length=11, validators=[only_int])
    telefone = models.CharField(max_length=11, validators=[only_int])
    endereco = models.CharField(max_length=100)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=20)
    UF = models.CharField(max_length=2)
    cep = models.CharField(max_length=8, validators=[only_int])
    data_nasc = models.DateField()

    class Meta:
        verbose_name = 'Motorista'
        verbose_name_plural = 'Motorista'
        ordering=['nome']

    def __str__(self):
       return self.nome

class Veiculos(models.Model):
    CODIGOTPVEIC_CHOICES = [
        ('1', 'CAMINHÃO TOCO 3/4'),
        ('2', 'CAMINHÃO TOCO'),
        ('3', 'CAMINHÃO 3/4'),
        ('4', 'CAMINHONETE/UTILITARIO'),
        ('5', 'CAMINHÃO TRUCK'),
        ('6', 'PASSEIO'),
        ('7', 'CAVALO'),
        ('8', 'CARRETA'),
        ('9', 'CAMINHÃO BI TRUCK '),
        ('10', 'CAVALO '),
        ('11', 'CAMINHAO LEVE'),
        ('12', 'SEMI ROBOQUE'),
        ('13', 'CAMINHÃO FURGÃO'),
        ('14', 'CAMINHÃO TRUCK '),
        ('15', 'CAMINHOTE'),
        ('16', 'CAMINHONETE/FURGAO')
    ]

    codigoveic = models.BigAutoField(primary_key=True)
    codigotpveic = models.CharField(max_length=5, choices=CODIGOTPVEIC_CHOICES)
    filial = models.CharField(max_length=3, choices=TIPO_GARAGEM)
    prefixoveic = models.CharField(max_length=7, unique=True, error_messages={'unique':'Esta Placa já está cadastrada, gentileza verificar'})
    kmatualveic = models.IntegerField()
    obsveic = models.CharField(max_length=30, blank=True, null=True)
    renavanveic = models.CharField(max_length=11, validators=[only_int])
    modeloveic = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Veiculos'
        verbose_name_plural = 'Veiculos'

    def __str__(self):
       return self.prefixoveic

class ChecklistFrota(models.Model):
    idchecklist = models.BigAutoField(primary_key=True)
    datachecklist = models.DateField(default=timezone.now)
    placaveic = models.ForeignKey(Veiculos, on_delete=models.CASCADE)
    motoristaveic = models.ForeignKey(Motorista, on_delete=models.CASCADE)
    placacarreta = models.CharField(max_length=7, blank=True, null=True)
    placacarreta2 = models.CharField(max_length=7, blank=True, null=True)
    kmanterior = models.IntegerField()
    kmatual = models.IntegerField()
    horimetro = models.CharField(max_length=10)
    p1_1 = models.BooleanField('Uniforme da Empresa')
    p1_2 = models.BooleanField('Motorista identificado por crachá')
    p2_1 = models.BooleanField('Lanterna do farol dianteiro funcionando?')
    p2_2 = models.BooleanField('Farol baixo funcionando?')
    p2_3 = models.BooleanField('Farol alto funcionando?')
    p2_4 = models.BooleanField('Lanterna direita funcionando?')
    p2_5 = models.BooleanField('Lanterna esquerda funcionando?')
    p2_6 = models.BooleanField('Lanternas traseiras funcionando?')
    p2_7 = models.BooleanField('Luz de ré funcionando?')
    p2_8 = models.BooleanField('Retrovisores estão em perfeito estado?')
    p2_9 = models.BooleanField('Água do radiador está no nível?')
    p2_10 = models.BooleanField('Óleo de freio está no nível?')
    p2_11 = models.BooleanField('Óleo de motor está no nível?')
    p2_12 = models.BooleanField('Verificado todas as luzes de advertências?')
    p2_13 = models.BooleanField('Verificado o freio de emergência?')
    p2_14 = models.BooleanField('Verificado o alarme sonoro da ré?')
    p2_15 = models.BooleanField('Verificado se existe vazamentos de óleo de motor?')
    p2_16 = models.BooleanField('Verificado se existe vazamento de ar?')
    p2_17 = models.BooleanField('Verificado se existe vazamento de óleo hidráulico?')
    p2_18 = models.BooleanField('Verificado se existe vazamento de água no radiador?')
    p2_19 = models.BooleanField('Verificado se as mangueiras estão em condições boas?')
    p2_20 = models.BooleanField('Pneus em boas condições?')
    p2_21 = models.BooleanField('As lonas de freio estão em boas condições?')
    p2_22 = models.BooleanField('Os estepes estão bons?')
    p2_23 = models.BooleanField('A suspensão está em condições perfeitas?')
    p2_24 = models.BooleanField('O carro está limpo e higienizado?')
    p3_1 = models.BooleanField('Foi verificado as luzes de advertência das laterais?')
    p3_2 = models.BooleanField('Foi verificado o lacre da placa?')
    p3_3 = models.BooleanField('Foi verificado se o aparelho thermoking apresenta falhas?')
    p3_4 = models.BooleanField('Foi verificado a carroceria, assoalho e baú?')
    p3_5 = models.BooleanField('Foi verificado a luz de freio?')
    p3_6 = models.BooleanField('Foi verificado a luz de ré?')
    p3_7 = models.BooleanField('Foi verificado se as luzes da lanterna traseira direita funciona?')
    p3_8 = models.BooleanField('Foi verificado se as luzes da lanterna traseira esquerda funciona?')
    obs = models.TextField('Observação', blank=True)
    autor = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'ChecklistFrota'
        verbose_name_plural = 'ChecklistFrota'

    def __str__(self):
       return str(self.idchecklist)

class TipoServicosManut(models.Model):
    id = models.BigAutoField(primary_key=True)
    grupo_servico = models.CharField('Grupo', max_length=50)
    tipo_servico = models.CharField('Tipo Servico', max_length=50)

class FuncPj(models.Model):
    PESSOA_FISICA = 'PF'
    PESSOA_JURIDICA = 'PJ'
    TIPO_CONTRATO_CHOICES = [
        (PESSOA_FISICA, 'PF'),
        (PESSOA_JURIDICA, 'PJ'),
    ]

    id = models.BigAutoField(primary_key=True)
    filial = models.CharField(choices=TIPO_GARAGEM, max_length=3, blank=True, null=True)
    nome = models.CharField(max_length=50)
    salario = models.FloatField(blank=True, null=True)
    adiantamento = models.FloatField(blank=True, null=True)
    ajuda_custo = models.FloatField(blank=True, null=True)
    cpf_cnpj = models.CharField(max_length=14, validators=[only_int])
    tipo_contrato = models.CharField(choices=TIPO_CONTRATO_CHOICES, max_length=2)
    banco = models.CharField(max_length=50 ,blank=True, null=True)
    ag = models.IntegerField(blank=True, null=True)
    conta = models.IntegerField(blank=True, null=True)
    op = models.IntegerField(blank=True, null=True)
    email = models.EmailField(max_length=254)
    admissao = models.DateField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Funcpj'
        verbose_name_plural = 'Funcpj'

    def __str__(self):
       return self.nome

class NfServicoPj(models.Model):
    id = models.BigAutoField(primary_key=True)
    funcionario = models.ForeignKey(FuncPj, on_delete=PROTECT)
    faculdade = models.FloatField()
    cred_convenio = models.FloatField()
    outros_cred = models.FloatField()
    desc_convenio = models.FloatField()
    outros_desc = models.FloatField()
    data_pagamento = models.DateField()
    data_emissao = models.DateField(default=timezone.now)
    autor = models.ForeignKey(User, on_delete=PROTECT)

    class Meta:
        verbose_name = 'NfServicoPj'
        verbose_name_plural = 'NfServicoPj'

    def __str__(self):
       return str(self.id)

class MailsPJ(models.Model):
    id = models.BigAutoField(primary_key=True)
    funcionario = models.ForeignKey(FuncPj, on_delete=PROTECT)
    data_envio = models.DateTimeField(default=timezone.now)
    data_pagamento = models.DateField()
    mensagem = models.TextField()


class pj13(models.Model):
    id = models.BigAutoField(primary_key=True)
    periodo_meses = models.IntegerField()
    valor = models.FloatField(blank=True, null=True)
    pgto_parc_1 = models.DateField()
    pgto_parc_2 = models.DateField(blank=True, null=True)
    funcionario = models.ForeignKey(FuncPj, on_delete=PROTECT)
    autor = models.ForeignKey(User, on_delete=PROTECT)

class feriaspj(models.Model):
    PGTO_CHOICES = [
        ('INTEGRAL','INTEGRAL'),
        ('PARCIAL','PARCIAL')
    ]
    id = models.BigAutoField(primary_key=True)
    ultimas_ferias_ini = models.DateField()
    ultimas_ferias_fim = models.DateField()
    periodo = models.CharField(max_length=2, validators=[only_int],blank=True, null=True)
    quitado = models.BooleanField(default=0)
    funcionario = models.ForeignKey(FuncPj, on_delete=PROTECT, blank=True)
    vencimento = models.DateField()
    tp_pgto = models.CharField(max_length=8, choices=PGTO_CHOICES)
    agendamento_ini = models.DateField(blank=True, null=True)
    agendamento_fim = models.DateField(blank=True, null=True)
    valor_integral = models.FloatField(blank=True, null=True)
    valor_parcial1 = models.FloatField(blank=True, null=True)
    valor_parcial2 = models.FloatField(blank=True, null=True)
    dt_quitacao = models.DateField(blank=True, null=True)
    alerta_venc_enviado = models.BooleanField(default=0)

    def __str__(self):
       return self.funcionario.nome

class ManutencaoFrota(models.Model):
    TIPO_MANUTENCAO_CHOICES = [
        ('PREVENTIVA', 'PREVENTIVA'),
        ('CORRETIVA', 'CORRETIVA')
    ]
    FILIAL_CHOICES = [
        ('SPO', 'SPO'),
        ('VDC', 'VDC')
    ]
    LOCAL_MANU_CHOICES = [
        ('I','INTERNO'),
        ('E','EXTERNO')
    ]
    STATUS_CHOICES = [
        ('ANDAMENTO', 'ANDAMENTO'),
        ('PENDENTE', 'PENDENTE'),
        ('CONCLUIDO', 'CONCLUIDO')
    ]

    id = models.BigAutoField(primary_key=True)
    veiculo = models.ForeignKey(Veiculos, on_delete=PROTECT)
    tp_manutencao = models.CharField('Tipo manutenção',max_length=10,choices=TIPO_MANUTENCAO_CHOICES)
    local_manu = models.CharField('Local manutenção',max_length=1, choices=LOCAL_MANU_CHOICES)
    dt_ult_manutencao = models.DateField('Data da última manutenção', blank=True, null=True)
    dt_entrada = models.DateField()
    dt_saida = models.DateField(blank=True, null=True)
    dias_veic_parado = models.CharField(max_length=20, blank=True, null=True)
    km_ult_troca_oleo = models.IntegerField('Kilometragem da última troca de óleo')
    tp_servico = models.CharField('Tipo serviço', max_length=10)
    valor_maodeobra = models.FloatField('Valor mão de obra', blank=True, null=True)
    valor_peca = models.FloatField('Valor peça', blank=True, null=True)
    filial = models.CharField(max_length=3, choices=FILIAL_CHOICES)
    socorro = models.BooleanField()
    prev_entrega = models.DateField()
    observacao = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    autor = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'ManutencaoFrota'
        verbose_name_plural = 'ManutencaoFrota'

    def __str__(self):
        return str(self.id)

class ServJoinManu(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_os = models.ForeignKey(ManutencaoFrota, on_delete=PROTECT)
    id_svs = models.ForeignKey(TipoServicosManut, on_delete=PROTECT)
    pub_date = models.DateField(auto_now=True)
    autor = models.ForeignKey(User, on_delete=PROTECT)

    class Meta:
        verbose_name = 'ServJoinManu'
        verbose_name_plural = 'ServJoinManu'

    def __str__(self):
        return (str(self.id_os) + ' ' + str(self.id_svs))

class CardFuncionario(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    empresa = models.CharField(max_length=30)
    cargo = models.CharField(max_length=20)
    email = models.EmailField(max_length=255)
    celular = models.CharField(max_length=11,validators=[only_int])
    foto = models.ImageField(upload_to='images/', null=True)

    def __str__(self):
        return self.nome

class TicketMonitoramento(models.Model):
    STATUS_CHOICES = [
        ('ABERTO', 'ABERTO'),
        ('ANDAMENTO', 'ANDAMENTO'),
        ('CONCLUIDO', 'CONCLUIDO'),
        ('CANCELADO', 'CANCELADO')
    ]
    CATEGORIA_CHOICES = [
        ('Aguardando Recebimento','Aguardando Recebimento'),
        ('Dae','Dae'),
        ('Descarga','Descarga'),
        ('Devolução Parcial','Devolução Parcial'),
        ('Devolução Total','Devolução Total'),
        ('Diaria autorizada','Diaria autorizada'),
        ('Dif. Peso','Dif. Peso'),
        ('Entrega Realizada','Entrega Realizada'),
        ('Fora de Horário','Fora de Horário'),
        ('Fora de Rota','Fora de Rota'),
        ('Imprópria','Imprópria'),
        ('Merc. nao embar.','Merc. nao embar.'),
        ('Prorrogação de Boleto','Prorrogação de Boleto'),
        ('Reentrega','Reentrega'),
        ('Refaturamento','Refaturamento'),
        ('Reversa','Reversa'),
        ('Sem Agendamento','Sem Agendamento'),
        ('Sem Pedido','Sem Pedido'),
        ('Veículo em rota','Veículo em rota'),
        ('Veículo Quebrado','Veículo Quebrado')
    ]
    id = models.BigAutoField(primary_key=True)
    nome_tkt = models.CharField(max_length=100, unique=True, error_messages={'unique':'Já existe ticket criado para este CTE'})
    dt_abertura = models.DateField()
    responsavel = models.ForeignKey(User, on_delete=PROTECT, related_name='responsavel')
    solicitante = models.ForeignKey(User, on_delete=PROTECT, related_name='solicitante')
    remetente = models.CharField(max_length=50)
    destinatario = models.CharField(max_length=50)
    cte = models.CharField(max_length=100)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES)
    status = models.CharField(max_length=9, choices=STATUS_CHOICES)
    msg_id = models.CharField(max_length=100, unique=True)

class EmailMonitoramento(models.Model):
    id = models.BigAutoField(primary_key=True)
    assunto = models.CharField(max_length=100)
    mensagem = models.TextField()
    cc = models.CharField(max_length=1000, blank=True, null=True)
    dt_envio = models.DateField()
    email_id = models.CharField(max_length=100, unique=True)
    ult_resp = models.TextField(blank=True, null=True)
    ult_resp_dt = models.DateField(blank=True, null=True)
    ult_resp_html = models.TextField(blank=True, null=True)
    tkt_ref = models.ForeignKey(TicketMonitoramento, on_delete=PROTECT)

class TicketChamado(models.Model):
    SERVICO_CHOICES = [
        ('DESENVOLVIMENTO', 'DESENVOLVIMENTO'),
        ('TI','TI'),
        ('PRAXIO','PRAXIO'),
        ('MANUTENCAO','MANUTENCAO')
    ]
    STATUS_CHOICES = [
        ('ABERTO', 'ABERTO'),
        ('ANDAMENTO', 'ANDAMENTO'),
        ('CONCLUIDO', 'CONCLUIDO'),
        ('CANCELADO', 'CANCELADO')
    ]
    DEPARTAMENTO_CHOICES = [
        ('DIRETORIA', 'DIRETORIA'),
        ('FATURAMENTO', 'FATURAMENTO'),
        ('FINANCEIRO', 'FINANCEIRO'),
        ('RH', 'RH'),
        ('FISCAL', 'FISCAL'),
        ('MONITORAMENTO', 'MONITORAMENTO'),
        ('OPERACIONAL', 'OPERACIONAL'),
        ('FROTA', 'FROTA'),
        ('EXPEDICAO', 'EXPEDICAO'),
        ('COMERCIAL', 'COMERCIAL'),
        ('JURIDICO', 'JURIDICO'),
        ('DESENVOLVIMENTO', 'DESENVOLVIMENTO'),
        ('TI', 'TI'),
        ('FILIAIS', 'FILIAIS')
    ]
    id = models.BigAutoField(primary_key=True)
    solicitante = models.CharField(max_length=100)
    responsavel = models.ForeignKey(User, on_delete=PROTECT, blank=True, null=True)
    servico = models.CharField(max_length=15,choices=SERVICO_CHOICES)
    nome_tkt = models.CharField(max_length=150)
    dt_abertura = models.DateTimeField()
    filial = models.CharField(max_length=3, choices=TIPO_GARAGEM, blank=True, null=True)
    departamento = models.CharField(max_length=15, choices=DEPARTAMENTO_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=9, choices=STATUS_CHOICES)
    msg_id = models.CharField(max_length=100, unique=True)

class EmailChamado(models.Model):
    id = models.BigAutoField(primary_key=True)
    assunto = models.CharField(max_length=100)
    mensagem = models.TextField()
    cc = models.CharField(max_length=1000, blank=True, null=True)
    dt_envio = models.DateField()
    email_id = models.CharField(max_length=100, unique=True)
    ult_resp = models.TextField(blank=True, null=True)
    ult_resp_dt = models.DateField(blank=True, null=True)
    ult_resp_html = models.TextField(blank=True, null=True)
    tkt_ref = models.ForeignKey(TicketChamado, on_delete=PROTECT)

