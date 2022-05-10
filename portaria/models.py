import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, DecimalValidator, MinLengthValidator
from django.db import models
from django.db.models import PROTECT, Sum, F
from django.utils import timezone
from django.utils.crypto import get_random_string

MAIL_CHOICES = [
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
    ]

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
    ('TMA','TMA'),
    ('VIX','VIX'),
)
TIPO_DOCTO_CHOICES = (
    ('8', 'NFS'),
    ('57', 'CTE')
)
GARAGEM_CHOICES = [
        ('1', 'SPO'),
        ('2', 'REC'),
        ('3', 'SSA'),
        ('4', 'FOR'),
        ('5', 'MCZ'),
        ('6', 'NAT'),
        ('7', 'JPA'),
        ('8', 'AJU'),
        ('9', 'VDC'),
        ('10', 'MG'),
        ('20', 'CTG'),
        ('21', 'TCO'),
        ('22', 'UDI'),
        ('23', 'TMA'),
        ('24', 'VIX'),
        ('30', 'BMA'),
        ('31', 'BPE'),
        ('32', 'BEL'),
        ('33', 'BPB'),
        ('34', 'SLZ'),
        ('35', 'BAL'),
        ('36', 'THE'),
        ('40', 'FMA')
    ]
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
    notas = models.IntegerField()
    kilometragem = models.IntegerField()
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
    palete = models.ForeignKey(PaleteControl, on_delete=models.CASCADE)
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
    GARAGEM_CHOICES = [
        ('1', 'SPO'),
        ('2', 'REC'),
        ('3', 'SSA'),
        ('4', 'FOR'),
        ('5', 'MCZ'),
        ('6', 'NAT'),
        ('7', 'JPA'),
        ('8', 'AJU'),
        ('9', 'VDC'),
        ('10', 'MG'),
        ('20', 'CTG'),
        ('21', 'TCO'),
        ('22', 'UDI'),
        ('23', 'TMA'),
        ('24', 'VIX'),
        ('30', 'BMA'),
        ('31', 'BPE'),
        ('32', 'BEL'),
        ('33', 'BPB'),
        ('34', 'SLZ'),
        ('35', 'BAL'),
        ('36', 'THE')
    ]

    idchecklist = models.BigAutoField(primary_key=True)
    datachecklist = models.DateField(default=timezone.now)
    placaveic = models.ForeignKey(Veiculos, on_delete=models.CASCADE)
    motoristaveic = models.ForeignKey(Motorista, on_delete=models.CASCADE)
    placacarreta = models.CharField(max_length=7, blank=True, null=True)
    placacarreta2 = models.CharField(max_length=7, blank=True, null=True)
    kmanterior = models.IntegerField()
    kmatual = models.IntegerField()
    horimetro = models.CharField(max_length=10)
    filial = models.CharField(max_length=2, choices=GARAGEM_CHOICES)
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
    p2_12 = models.BooleanField('Bateria em boas condições?')
    p2_13 = models.BooleanField('Freio de emergência funcionando?')
    p2_14 = models.BooleanField('Alarme sonoro da ré funcionando?')
    p2_15 = models.BooleanField('Existe vazamentos de óleo de motor?')
    p2_16 = models.BooleanField('Existe vazamentos de ar?')
    p2_17 = models.BooleanField('Existe vazamento de óleo hidráulico?')
    p2_18 = models.BooleanField('Existe vazamento de água no radiador?')
    p2_19 = models.BooleanField('As mangueiras estão em boas condições?')
    p2_20 = models.BooleanField('Lonas de freio em boas condições?')
    p2_21 = models.BooleanField('Amortecedor em boas condições?')
    p2_22 = models.BooleanField('A suspensão está em boas condições?')
    p2_23 = models.BooleanField('O carro está limpo e higienizado?')
    p2_24 = models.BooleanField('Limpador de parabrisa funcionando?')
    p2_25 = models.BooleanField('Parabrisa em boas condições?')
    p2_26 = models.BooleanField('Ar condicionado funcionando?')
    p2_27 = models.BooleanField('Pintura do cavalo em boas condições?')
    p2_28 = models.BooleanField('Extintor em boas condições?')
    p2_29 = models.BooleanField('Pneus dianteiros em bom estado?')
    p2_30 = models.BooleanField('Pneus tração em bom estado?')
    p2_31 = models.BooleanField('Pneus traseiros em bom estado?')
    p2_32 = models.BooleanField('Lubrificação está em bom estado?')
    p2_33 = models.BooleanField('Alinhamento está em bom estado?')
    p2_34 = models.BooleanField('Balanceamento está em bom estado?')
    obs_cavalo = models.TextField('Obs Cavalo', blank=True)
    p3_1 = models.BooleanField('Luzes de advertência das laterais funcionando?')
    p3_2 = models.BooleanField('Estepes em bom estado?')
    p3_3 = models.BooleanField('Thermoking está em boas condições?')
    p3_4 = models.BooleanField('Carroceria, assoalho e baú em boas condições?')
    p3_5 = models.BooleanField('Luz de freio funcionando?')
    p3_6 = models.BooleanField('Luz de ré funcionando?')
    p3_7 = models.BooleanField('Luzes da lanterna traseira direita funciona?')
    p3_8 = models.BooleanField('Luzes da lanterna traseira esquerda funciona?')
    p3_9 = models.BooleanField('Veículo plotado?')
    p3_10 = models.BooleanField('Plotagem em boas condições?')
    p3_11 = models.BooleanField('Amortecedores em boas condições?')
    p3_12 = models.BooleanField('A carreta está lavada?')
    p3_13 = models.BooleanField('Pneus dianteiros em bom estado?')
    p3_14 = models.BooleanField('Pneus tração em bom estado?')
    p3_15 = models.BooleanField('Pneus traseiros em bom estado?')
    p3_16 = models.BooleanField('Lubrificação em boas condições?')
    p3_17 = models.BooleanField('Alinhamento em boas condições?')
    p3_18 = models.BooleanField('Balanceamento em boas condições?')
    p3_19 = models.BooleanField('Carreta tem divisória?')
    obs_carreta = models.TextField('Obs Carreta', blank=True)
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
    aux_moradia = models.FloatField()
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
        ('CORRETIVA', 'CORRETIVA'),
        ('PRE','PRE')
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
    motorista = models.CharField(max_length=50, blank=True, null=True)
    tp_manutencao = models.CharField('Tipo manutenção',max_length=10,choices=TIPO_MANUTENCAO_CHOICES,blank=True, null=True)
    local_manu = models.CharField('Local manutenção',max_length=1, choices=LOCAL_MANU_CHOICES,blank=True, null=True)
    dt_ult_manutencao = models.DateField('Data da última manutenção', blank=True, null=True)
    dt_entrada = models.DateField(blank=True, null=True)
    dt_ini_manu = models.DateField('Inicio Manutencao',blank=True, null=True)
    dt_saida = models.DateField(blank=True, null=True)
    dias_veic_parado = models.CharField(max_length=20, blank=True, null=True)
    km_atual = models.IntegerField('Kilometragem atual',blank=True, null=True)
    filial = models.CharField(max_length=3, choices=FILIAL_CHOICES,blank=True, null=True)
    socorro = models.BooleanField(default=False)
    prev_entrega = models.DateField(blank=True, null=True)
    observacao = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES,blank=True, null=True)
    autor = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'ManutencaoFrota'
        verbose_name_plural = 'ManutencaoFrota'

    def __str__(self):
        return str(self.id)

class ServJoinManu(models.Model):
    LOCAL_MANU_CHOICES = [
        ('I', 'INTERNO'),
        ('E', 'EXTERNO')
    ]
    id = models.BigAutoField(primary_key=True)
    id_os = models.ForeignKey(ManutencaoFrota, on_delete=PROTECT)
    id_svs = models.ForeignKey(TipoServicosManut, on_delete=PROTECT)
    valor_maodeobra = models.FloatField('Valor mão de obra', blank=True, null=True)
    valor_peca = models.FloatField('Valor peça', blank=True, null=True)
    produto = models.CharField(max_length=100, blank=True, null=True)
    fornecedor = models.CharField(max_length=100, blank=True, null=True)
    local_manu = models.CharField('Local manutenção', max_length=1, choices=LOCAL_MANU_CHOICES)
    feito = models.BooleanField(null=True)
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
    GARAGEM_CHOICES = [
        ('1', 'SPO'),
        ('2', 'REC'),
        ('3', 'SSA'),
        ('4', 'FOR'),
        ('5', 'MCZ'),
        ('6', 'NAT'),
        ('7', 'JPA'),
        ('8', 'AJU'),
        ('9', 'VDC'),
        ('10', 'MG'),
        ('20', 'CTG'),
        ('21', 'TCO'),
        ('22', 'UDI'),
        ('23', 'TMA'),
        ('24', 'VIX'),
        ('30', 'BMA'),
        ('31', 'BPE'),
        ('32', 'BEL'),
        ('33', 'BPB'),
        ('34', 'SLZ'),
        ('35', 'BAL'),
        ('36', 'THE')
    ]
    id = models.BigAutoField(primary_key=True)
    nome_tkt = models.CharField(max_length=150, unique=True, error_messages={'unique':'Já existe ticket criado para este CTE'})
    dt_abertura = models.DateField()
    responsavel = models.ForeignKey(User, on_delete=PROTECT, related_name='responsavel')
    solicitante = models.ForeignKey(User, on_delete=PROTECT, related_name='solicitante')
    remetente = models.CharField(max_length=100)
    destinatario = models.CharField(max_length=100)
    filial = models.CharField(max_length=3, choices=GARAGEM_CHOICES)
    cte = models.CharField(max_length=100)
    tp_docto = models.CharField(max_length=3, choices=TIPO_DOCTO_CHOICES)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES)
    status = models.CharField(max_length=9, choices=STATUS_CHOICES)
    msg_id = models.CharField(max_length=100, unique=True)

class EmailMonitoramento(models.Model):
    id = models.BigAutoField(primary_key=True)
    assunto = models.CharField(max_length=150)
    mensagem = models.TextField()
    cc = models.CharField(max_length=1000, blank=True, null=True)
    dt_envio = models.DateTimeField()
    email_id = models.CharField(max_length=100, unique=True)
    ult_resp = models.TextField(blank=True, null=True)
    ult_resp_dt = models.DateTimeField(blank=True, null=True)
    ult_resp_html = models.TextField(blank=True, null=True)
    tkt_ref = models.ForeignKey(TicketMonitoramento, on_delete=PROTECT)

class EmailOcorenciasMonit(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.CharField(max_length=255)
    rsocial = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)

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
    dt_envio = models.DateTimeField(blank=True, null=True)
    email_id = models.CharField(max_length=100, unique=True)
    ult_resp = models.TextField(blank=True, null=True)
    ult_resp_dt = models.DateTimeField(blank=True, null=True)
    ult_resp_html = models.TextField(blank=True, null=True)
    tkt_ref = models.ForeignKey(TicketChamado, on_delete=PROTECT)

class RomXML(models.Model):
    id = models.BigAutoField(primary_key=True)
    dt_emissao = models.DateTimeField()
    nota_fiscal = models.IntegerField()
    remetente = models.CharField(max_length=200)
    destinatario = models.CharField(max_length=200)
    peso = models.FloatField()
    volume = models.IntegerField()
    vlr_nf = models.FloatField()
    municipio = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)
    autor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    printed = models.BooleanField(default=False)
    pub_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.id)

class SkuRefXML(models.Model):
    id = models.BigAutoField(primary_key=True)
    codigo = models.CharField(max_length=30)
    desc_prod = models.CharField(max_length=200)
    tp_un = models.CharField(max_length=10)
    qnt_un = models.IntegerField()
    xmlref = models.ForeignKey(RomXML, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.xmlref_id)

class EtiquetasDocumento(models.Model):
    TIPO_DOCTO_CHOICES = (
        ('8', 'NFS'),
        ('57', 'CTE')
    )
    id = models.BigAutoField(primary_key=True)
    garagem = models.CharField(max_length=3, choices=GARAGEM_CHOICES)
    tp_doc = models.CharField(max_length=3, choices=TIPO_DOCTO_CHOICES)
    nr_doc = models.CharField(max_length=20)
    nota = models.CharField(max_length=10)
    volume = models.PositiveSmallIntegerField()
    pub_date = models.DateField(default=timezone.now)

    def __str__(self):
        return str(self.id)

class BipagemEtiqueta(models.Model):
    id = models.BigAutoField(primary_key=True)
    cod_barras = models.CharField(max_length=20)
    nota = models.CharField(max_length=10)
    doc_ref = models.ForeignKey(EtiquetasDocumento, on_delete=models.CASCADE)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    pub_date = models.DateField(default=timezone.now)

class RetornoEtiqueta(models.Model):
    id = models.BigAutoField(primary_key=True)
    nota_fiscal = models.CharField(max_length=15, unique=True)
    saida = models.DateField(default=timezone.now)

class EtiquetasPalete(models.Model):
    id = models.BigAutoField(primary_key=True)
    cod_barras = models.CharField(max_length=20)
    filial = models.CharField(max_length=3, choices=GARAGEM_CHOICES)
    cliente = models.CharField(max_length=200)
    volumes = models.IntegerField()
    pub_date = models.DateTimeField(default=timezone.now)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)

class BipagemPalete(models.Model):
    id = models.BigAutoField(primary_key=True)
    filial = models.CharField(max_length=3, choices=GARAGEM_CHOICES)
    bip_date = models.DateTimeField(default=timezone.now)
    cod_barras = models.CharField(max_length=20)
    volume_conf = models.IntegerField(blank=True, null=True)
    manifesto = models.IntegerField(blank=True, null=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    etq_ref = models.ForeignKey(EtiquetasPalete, on_delete=models.CASCADE)

class JustificativaEntrega(models.Model):
    JUSTIFICATIVA_CHOICES = (
        ('143', 'FERIADO NACIONAL'),
        ('144', 'FERIADOS MUNICIPAIS / ESTADUAIS'),
        ('145', 'ENTREGA AGENDADA'),
        ('146', 'CLIENTE COM RETENÇÃO FISCAL'),
        ('147', 'DESTINATARIO NÃO RECEBEU O XML'),
        ('148', 'NF SEM PEDIDO'),
        ('149', 'PEDIDO EXPIRADO'),
        ('150', 'EXCESSO DE VEICULOS'),
        ('151', 'GRADE FIXA'),
        ('152', 'DEVOLUÇÃO TOTAL '),
        ('153', 'ATRASO NA TRANSFERENCIA'),
        ('154', 'CUSTO'),
        ('155', 'OCORRENCIA OPERACIONAL INTERNA')
    )
    empresa = models.CharField(max_length=5)
    filial = models.CharField(max_length=5)
    garagem = models.CharField(max_length=5)
    id_garagem = models.CharField(max_length=5)
    conhecimento = models.CharField(max_length=15)
    data_emissao = models.DateField()
    destinatario = models.CharField(max_length=200)
    remetente = models.CharField(max_length=200)
    peso = models.FloatField()
    lead_time = models.DateField()
    em_aberto = models.SmallIntegerField()
    local_entreg = models.CharField(max_length=100)
    nota_fiscal = models.CharField(max_length=200)
    tipo_doc = models.CharField(max_length=5)
    cod_just = models.CharField(max_length=3, blank=True, null=True)
    desc_just = models.CharField(max_length=100, blank=True, null=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

class OcorrenciaEntrega(models.Model):
    empresa = models.CharField(max_length=5)
    filial = models.CharField(max_length=5)
    garagem = models.CharField(max_length=5)
    conhecimento = models.CharField(max_length=15)
    tp_doc = models.CharField(max_length=5)
    cod_ocor = models.CharField(max_length=5)
    desc_ocor = models.CharField(max_length=200)
    data_ocorrencia = models.DateField()
    entrega = models.ForeignKey(JustificativaEntrega, on_delete=models.CASCADE, blank=True, null=True)

