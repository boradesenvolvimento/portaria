#imports geral
import random
import csv
import datetime
import email, smtplib
import os
import re
import textwrap
import poplib
from email import policy
from email.header import decode_header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import pandas as pd
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import make_msgid

from notifications.models import Notification
from notifications.signals import notify
#imports django built-ins
from PIL import Image
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Count, Sum, F, Q, Value, Subquery, CharField, ExpressionWrapper, IntegerField, \
    DateTimeField
from django.db.models.functions import Coalesce, TruncDate, Cast, TruncMinute
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.template.defaultfilters import upper
from django.urls import reverse
from django.utils import timezone
from django.views import generic


#imports django projeto
from .dbtest import conndb
from .models import * #Cadastro, PaletControl, ChecklistFrota, Veiculos, NfServicoPj
from .forms import * #CadastroForm, isPlacaForm, DateForm, FilterForm, TPaletsForm, TIPO_GARAGEM, ChecklistForm
from mysite.settings import get_secret


def telausuariothiago(request):
    return render(request, "portaria/telausuariothiago.html")

def telausuariorodrigo(request):
    return render(request, "portaria/telausuariorodrigo.html")

def cardusuario(request):
    form = CardFuncionario.objects.all()
    src = request.GET.get('srcfunc')
    if src:
        try:
            src1 = CardFuncionario.objects.filter(nome__contains=src)
        except ObjectDoesNotExist:
            messages.error(request, 'Não encontrado')
            return render(request, 'portaria/card/cardusuario.html', {'form':form})
        else:
            form = src1
            return render(request, 'portaria/cardusuario.html',{'form':form})
    return render(request, 'portaria/card/cardusuario.html', {'form':form})

def card(request, id):
    idcard = get_object_or_404(CardFuncionario, pk=id)
    form = CardFuncionario.objects.get(pk=idcard.id)
    return render(request, 'portaria/card/card.html', {'form':form})

#views
@login_required
def index(request):
    return render(request, "portaria/etc/index.html")

class Visualizacao(generic.ListView):
    paginate_by = 10
    template_name = 'portaria/portaria/visualizacao.html'
    context_object_name = 'lista'
    form = DateForm()

    def get_queryset(self):
        autor = self.request.user
        if autor.is_staff:
            qs = Cadastro.objects.all().filter(hr_chegada__month=datetime.datetime.now().month,hr_chegada__year=datetime.datetime.now().year).order_by('-hr_chegada')
        else:
            qs = Cadastro.objects.all().filter(hr_chegada__month=datetime.datetime.now().month,hr_chegada__year=datetime.datetime.now().year, autor=autor).order_by('-hr_chegada')
        try:
            form_input1 = self.request.GET.get('date')
            form_input2 = self.request.GET.get('date1')
            if form_input1 and form_input2:
                self.dateparse1 = datetime.datetime.strptime(form_input1, '%Y-%m-%d').replace(hour=00, minute=00)
                self.dateparse2 = datetime.datetime.strptime(form_input2, '%Y-%m-%d').replace(hour=23, minute=59)
                if autor.is_staff:
                    qs = Cadastro.objects.all().filter(hr_chegada__gte=self.dateparse1,
                                                       hr_chegada__lte=self.dateparse2).order_by('-hr_chegada')
                else:
                    qs = Cadastro.objects.all().filter(hr_chegada__gte=self.dateparse1,
                                                       hr_chegada__lte=self.dateparse2, autor=autor).order_by('-hr_chegada')
        except ValueError:
            raise Exception('Valor digitado inválido')
        return qs

    def get_context_data(self, **kwargs):
        context = super(Visualizacao, self).get_context_data(**kwargs)
        context['form'] = DateForm()
        return context

@login_required
def cadastroentrada(request):
    if request.user.is_authenticated:
        form = CadastroForm(request.POST or None)
        autor = request.user
        if request.method == 'POST':
            if form.is_valid():
                uplaca = upper(form.cleaned_data['placa'])
                order = form.save(commit=False)
                order.placa = uplaca
                order.autor = autor
                order.hr_chegada = datetime.datetime.now()
                order.save()
                messages.success(request,'Entrada cadastrada com sucesso.')
                return redirect('portaria:cadastro')
        return render(request, 'portaria/portaria/cadastroentrada.html', {'cadastro': cadastro, 'form': form})
    else:
        auth_message = 'Usuário não autenticado, por favor logue novamente'
        return render(request, 'portaria/portaria/cadastroentrada.html', {'auth_message': auth_message})

@login_required
def cadastrosaida(request):
    if request.user.is_authenticated:
        form_class = isPlacaForm
        form = form_class(request.POST or None)
        if request.method == 'POST':
            form = isPlacaForm(request.POST)
            if form.is_valid():
                s_query = upper(form.cleaned_data['search_placa'])
                q_query = upper(form.cleaned_data['search_dest'])
                days_back = timezone.now() - datetime.timedelta(days=30)
                loc_placa = Cadastro.objects.filter(placa=s_query, hr_chegada__gte=days_back,
                                                    hr_saida=None).order_by('-hr_chegada').first()
                try:
                    Cadastro.objects.get(pk=loc_placa.id)
                except AttributeError:
                    messages.error(request, 'Não encontrado')
                    return render(request, 'portaria/portaria/cadastrosaida.html', {'form':form})
                else:
                    Cadastro.objects.filter(pk=loc_placa.id).update(hr_saida=timezone.now(), destino=q_query, autor=request.user)
                    messages.success(request, 'Saida cadastrada com sucesso.')
                    return HttpResponseRedirect(reverse('portaria:cadastro'))
        return render(request, 'portaria/portaria/cadastrosaida.html', {'form':form})
    else:
        auth_message = 'Usuário não autenticado, por favor logue novamente'
        return render(request, 'portaria/portaria/cadastrosaida.html', {'auth_message': auth_message})

@login_required
def cadastro(request):
    if request.user.is_authenticated:
        filiais = TIPO_GARAGEM
        return render(request, 'portaria/portaria/cadastro.html', {'filiais':filiais})
    else:
        auth_message = 'Usuário não autenticado, por favor logue novamente'
        return render(request, 'portaria/portaria/cadastro.html', {'auth_message': auth_message})

@login_required
def outputs(request):
    return render(request, 'portaria/etc/outputs.html')


def paleteview(request):
    tp_fil = TIPO_GARAGEM
    tp_emp = Cliente.objects.values_list('razao_social', flat=True)
    form = PaleteControl.objects.values('loc_atual').annotate(pbr=Count('id', filter=Q(tp_palete='PBR')),chep=Count('id', filter=Q(tp_palete='CHEP'))).annotate(total=ExpressionWrapper(Count('id'), output_field=IntegerField()))
    ttcount = form.aggregate(total_amount=Sum('total'))
    fil = request.GET.get('filial')
    tp_p = request.GET.get('tp_palete')
    #switch case moral
    if fil and tp_p:
        #busca todos os campos
        form = PaleteControl.objects.filter(loc_atual=fil, tp_palete=tp_p).values('loc_atual').annotate(pbr=Count('id', filter=Q(tp_palete='PBR')),chep=Count('id', filter=Q(tp_palete='CHEP'))).annotate(total=ExpressionWrapper(Count('id'), output_field=IntegerField()))
        ttcount = form.aggregate(total_amount=Sum('total'))
    elif fil and not tp_p:
        #busca somente filial
        form = PaleteControl.objects.filter(loc_atual=fil).values('loc_atual').annotate(pbr=Count('id', filter=Q(tp_palete='PBR')),chep=Count('id', filter=Q(tp_palete='CHEP'))).annotate(total=ExpressionWrapper(Count('id'), output_field=IntegerField()))
        ttcount = form.aggregate(total_amount=Sum('total'))
    elif tp_p and not fil:
        #busca somente tipo do palete
        form = PaleteControl.objects.filter(tp_palete=tp_p).values('loc_atual').annotate(pbr=Count('id', filter=Q(tp_palete='PBR')),chep=Count('id', filter=Q(tp_palete='CHEP'))).annotate(total=ExpressionWrapper(Count('id'), output_field=IntegerField()))
        ttcount = form.aggregate(total_amount=Sum('total'))
    return render(request, 'portaria/palete/paletes.html', {'form':form,'tp_fil':tp_fil,'tp_emp':tp_emp,'ttcount':ttcount})

def cadpaletes(request):
    tp_fil = TIPO_GARAGEM
    tp_emp = Cliente.objects.all()
    if request.method == 'POST':
        qnt = request.POST.get('qnt')
        fil = request.POST.get('fil')
        emp = request.POST.get('emp')
        tp_p = request.POST.get('tp_p')
        if qnt and fil and emp and tp_p:
            try:
                int(qnt)
            except ValueError:
                messages.error(request,'Por favor digite um valor numérico para quantidade')
                return redirect('portaria:cadpaletes')
            else:
                nsal = Cliente.objects.filter(pk=emp).annotate(saldonew=Sum(F('saldo')+int(qnt)))

                Cliente.objects.filter(pk=emp).update(saldo=nsal[0].saldonew)
                for x in range(0,int(qnt)):
                    PaleteControl.objects.create(loc_atual=fil, tp_palete=tp_p, autor=request.user)
                    if x == 2000: break
                messages.success(request, f'{qnt} Paletes foram cadastrados com sucesso')

    return render(request, 'portaria/palete/cadpaletes.html', {'tp_fil':tp_fil, 'tp_emp':tp_emp})

def paletecliente(request):
    form = Cliente.objects.filter(intex='CLIENTE')
    tcount = form.aggregate(total=Sum('saldo'))
    return render(request, 'portaria/palete/paletecliente.html', {'form':form,'tcount':tcount})

def saidapalete(request):
    tp_fil = TIPO_GARAGEM
    tp_emp = Cliente.objects.all()
    if request.method == 'POST':
        qnt = int(request.POST.get('qnt'))
        fil = request.POST.get('fil')
        emp = request.POST.get('emp')
        tp_p = request.POST.get('tp_p')
        if qnt and fil and emp and tp_p:
            chk = Cliente.objects.get(pk=emp)
            Cliente.objects.filter(pk=emp).update(saldo=(chk.saldo - qnt))
            for q in range(0,qnt):
                PaleteControl.objects.filter(loc_atual=fil, tp_palete=tp_p).first().delete()
            messages.success(request, 'Saidas cadastradas com sucesso')
            return redirect('portaria:paletecliente')
    return render(request, 'portaria/palete/saidapalete.html', {'tp_fil':tp_fil,'tp_emp':tp_emp})

@login_required
def frota(request):
    form = ChecklistFrota.objects.all()
    motos = Motorista.objects.all()
    if request.method == "GET":
        pla = request.GET.get('placa_')
        mot = request.GET.get('moto_')
        if pla and mot != 'Selecione...':
            try:
                pla1 = Veiculos.objects.get(prefixoveic=pla)
                mot1 = Motorista.objects.get(pk=mot)
            except ObjectDoesNotExist:
                messages.error(request,'Cadastro não encontrado')
                return render(request, 'portaria/frota/frota.html')
            else:
                return redirect('portaria:checklistfrota', placa_id=pla1, moto_id=mot1.codigomot)
        elif pla and mot == 'Selecione...':
            messages.error(request, 'Insira o motorista')
            return render(request, 'portaria/frota/frota.html',{'form':form, 'motos':motos})
        elif mot and not pla:
            messages.error(request, 'Insira a placa')
            return render(request, 'portaria/frota/frota.html',{'form':form, 'motos':motos})
    return render(request, 'portaria/frota/frota.html',{'form':form, 'motos':motos})

@login_required
def checklistfrota(request, placa_id, moto_id):
    pla = get_object_or_404(Veiculos, prefixoveic=placa_id)
    mot = get_object_or_404(Motorista, pk=moto_id)
    context = {}
    form = ChecklistForm
    context['form'] = form
    if request.method == 'POST':
        form = ChecklistForm(request.POST)
        if form.is_valid():
            obar = form.save(commit=False)
            obar.placaveic = pla
            obar.kmanterior = pla.kmatualveic
            obar.motoristaveic = mot
            obar.autor = request.user
            obar.save()
            pla.kmatualveic = obar.kmatual
            pla.save()
            messages.success(request, f'Checklist para placa {pla} e motorista {mot} concluído!')
            return HttpResponseRedirect(reverse('portaria:frota'))
    return render(request,'portaria/frota/checklistfrota.html', {'form':form,'pla':pla, 'mot':mot})

def checklistview(request):
    form = ChecklistFrota.objects.all().order_by('-datachecklist')
    return render(request, 'portaria/frota/checklistview.html', {'form':form})

def checklistdetail(request, idckl):
    form = get_object_or_404(ChecklistFrota, pk=idckl)
    return render(request, 'portaria/frota/checklistdetail.html', {'form':form})


def cadfuncionariopj(request):
    form = FuncPjForm
    if request.method == 'POST':
        form = FuncPjForm(request.POST or None)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                raise ValidationError('Erro')
            else:
                messages.success(request, 'Cadastrado com sucesso')
                return redirect('portaria:servicospj')
    return render(request, 'portaria/pj/cadfuncionariopj.html', {'form':form})

def atualizarfunc(request):
    allfuncs = FuncPj.objects.all()
    fields = FuncPjForm
    func = request.GET.get('func')
    if func:
        getid = get_object_or_404(FuncPj, pk=func)
        fields = FuncPjForm(instance=getid)
        if request.method == 'POST':
            fields = FuncPjForm(request.POST or None,instance=getid)
            if fields.is_valid():
                try:
                    fields.save()
                except Exception as e:
                    print(e)
                else:
                    messages.success(request, 'Entrada cadastrada com sucesso.')
                    return redirect('portaria:atualizarfunc')
            else:
                messages.error(request, 'Algo deu errado, por favor contate seu administrador.')
                return redirect('portaria:index')
    return render(request, 'portaria/pj/atualizarfunc.html', {'fields':fields,'allfuncs':allfuncs,'func':func})


@login_required
def servicospj(request):
    func = request.GET.get('nomefunc')
    filter = request.GET.get('filter')
    qnt_funcs = FuncPj.objects.filter(ativo=True).order_by('nome')
    if func:
        qnt_funcs = FuncPj.objects.all().filter(nome__icontains=func, ativo=True)
    elif filter:
        qnt_funcs = FuncPj.objects.all().filter(ativo=True).order_by(filter)

    return render(request, 'portaria/pj/servicospj.html', {'qnt_funcs': qnt_funcs})

@login_required
def consultanfpj(request):
    arrya = []
    qnt_funcs = FuncPj.objects.filter(ativo=True)
    for q in qnt_funcs:
        query = FuncPj.objects.filter(pk=q.id) \
            .annotate(faculdade=Coalesce(Sum('nfservicopj__faculdade', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
            cred_convenio=Coalesce(Sum('nfservicopj__cred_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
            outros_cred=Coalesce(Sum('nfservicopj__outros_cred', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
            desc_convenio=Coalesce(Sum('nfservicopj__desc_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
            outros_desc=Coalesce(Sum('nfservicopj__outros_desc', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
            ) \
            .annotate(total=((F('salario') + F('ajuda_custo') + F('faculdade') + F('cred_convenio') + F('outros_cred')) - (F('adiantamento') + F('desc_convenio') + F('outros_desc'))))
        arrya.extend(query)
    return render(request, 'portaria/pj/consultanfpj.html', {'arrya': arrya})

@login_required
def cadservicospj(request, args):
    form = ServicoPjForm(request.POST or None)
    func = get_object_or_404(FuncPj, pk=args)
    autor = request.user
    if request.method == 'POST':
        if form.is_valid():
            calc = form.save(commit=False)
            calc.funcionario = func
            calc.autor = autor
            calc.save()
            messages.success(request, f'Valores cadastrados com sucesso para {calc.funcionario}')
            return HttpResponseRedirect(reverse('portaria:servicospj'))
    return render(request, 'portaria/pj/cadservicospj.html', {'form':form,'func':func})

def decimopj(request):
    allfunc = FuncPj.objects.filter(ativo=True).annotate(parc1=F('pj13__pgto_parc_1'),parc2=F('pj13__pgto_parc_2')).order_by('nome')
    func = request.GET.get('srcfunc')
    if func:
        allfunc = FuncPj.objects.filter(nome__icontains=func, ativo=True).annotate(parc1=F('pj13__pgto_parc_1'),parc2=F('pj13__pgto_parc_2')).order_by('nome')
        return render(request, 'portaria/pj/decimopj.html', {'allfunc': allfunc})
    return render(request,'portaria/pj/decimopj.html', {'allfunc':allfunc})

def caddecimo1(request, idfunc):
    func = get_object_or_404(FuncPj, pk=idfunc)
    sal = func.salario
    autor = request.user
    meses = request.POST.get('meses')
    parc = request.POST.get('pgto_parc')
    if parc and meses:
        val = ((sal/12)*float(meses))/2
        pj13.objects.create(valor=val,pgto_parc_1=timezone.now(),periodo_meses=meses,funcionario=func, autor=autor)
        messages.success(request, 'Cadastro primeira parcela feito com sucesso')
        return redirect('portaria:decimopj')
    return render(request, 'portaria/pj/caddecimo1.html', {'func': func})

def caddecimo2(request, idfunc):
    func = get_object_or_404(FuncPj, pk=idfunc)
    autor = request.user
    if pj13.objects.filter(funcionario=func, pgto_parc_2=None).exists():
        form = pj13.objects.get(funcionario=func)
        parc = request.GET.get('pgto_parc')
        if parc:
            pj13.objects.filter(funcionario=func).update(pgto_parc_2=timezone.now(), autor=autor)
            messages.success(request, 'Cadastro segunda parcela feito com sucesso')
            return redirect('portaria:decimopj')
        return render(request, 'portaria/pj/caddecimo2.html', {'func': func, 'form': form})

def decimoview(request):
    period = request.GET.get('filter')
    if period:
        if period == 'pgto_parcela_1':
            array = []
            allfuncs = FuncPj.objects.filter(ativo=True, pj13__pgto_parc_1__isnull=False,pj13__pgto_parc_2__isnull=True)
            for q in allfuncs:
                query = FuncPj.objects.filter(pk=q.id).annotate(valor=F('pj13__valor'),
                                                                parc_1=F('pj13__pgto_parc_1'),
                                                                parc_2=F('pj13__pgto_parc_2'),
                                                                periodo=F('pj13__periodo_meses'))
                array.extend(query)
            return render(request, 'portaria/pj/decimoview.html', {'allfuncs': allfuncs, 'array': array})
        elif period == 'pgto_parcela_2':
            array = []
            allfuncs = FuncPj.objects.filter(ativo=True, pj13__pgto_parc_2__isnull=False)
            for q in allfuncs:
                query = FuncPj.objects.filter(pk=q.id).annotate(valor=F('pj13__valor'),
                                                                parc_1=F('pj13__pgto_parc_1'),
                                                                parc_2=F('pj13__pgto_parc_2'),
                                                                periodo=F('pj13__periodo_meses'))
                array.extend(query)
            return render(request, 'portaria/pj/decimoview.html', {'allfuncs': allfuncs, 'array': array})
    return render(request, 'portaria/pj/decimoview.html')

def feriaspjv(request):
    return render(request,'portaria/pj/feriaspj.html')

def feriascad(request):
    form = feriaspjForm
    deadline = datetime.timedelta(weeks=40, days=85, hours=23, minutes=50, seconds=600)
    if request.method == 'POST':
        form = feriaspjForm(request.POST or None)
        if form.is_valid():
            fim = form.cleaned_data['ultimas_ferias_fim']
            ini = form.cleaned_data['ultimas_ferias_ini']
            per = str(fim - ini)
            prox = fim + deadline
            setval = form.save(commit=False)
            setval.periodo = per.split(' days')[0]
            setval.vencimento = prox
            setval.save()
            messages.success(request, 'Cadastrado com sucesso!')
            return redirect('portaria:feriaspjv')

    return render(request,'portaria/pj/feriascad.html', {'form':form})

def feriasview(request):
    hoje = datetime.date.today()
    dias = hoje + datetime.timedelta(days=60)
    aa = FuncPj.objects.filter(ativo=True).values_list('id', flat=True)
    qs = feriaspj.objects.filter(quitado=False, funcionario_id__in=aa).order_by('vencimento')
    name = request.POST.get('textbox')
    opt = request.POST.get('option')
    if name or opt:
        if name == '' and opt:
            if opt == 'Férias Vencidas':
                qs = feriaspj.objects.filter(quitado=False, funcionario_id__in=aa, vencimento__lte=hoje).order_by('vencimento')
                return render(request, 'portaria/pj/feriasview.html', {'qs': qs, 'dias': dias, 'hoje': hoje})
            elif opt == 'Próximas do vencimento':
                qs = feriaspj.objects.filter(quitado=False, funcionario_id__in=aa, vencimento__gte= hoje,vencimento__lte=dias).order_by('vencimento')
                return render(request, 'portaria/pj/feriasview.html', {'qs': qs, 'dias': dias, 'hoje': hoje})
            else:
                pass
        elif opt == '' and name:
            qs = feriaspj.objects.filter(quitado=False, funcionario_id__in=aa, funcionario__nome__contains=name).order_by('vencimento')
            return render(request, 'portaria/pj/feriasview.html', {'qs': qs, 'dias': dias, 'hoje': hoje})
        elif name and opt:
            if opt == 'Férias Vencidas':
                qs = feriaspj.objects.filter(quitado=False, funcionario_id__in=aa, vencimento__lte = hoje, funcionario__nome__contains=name).order_by('vencimento')
                return render(request, 'portaria/pj/feriasview.html', {'qs': qs,'dias':dias,'hoje':hoje})
            elif opt == 'Próximas do vencimento':
                qs = feriaspj.objects.filter(quitado=False, funcionario_id__in=aa, vencimento__gte= hoje,vencimento__lte=dias, funcionario__nome__contains=name).order_by('vencimento')
                return render(request, 'portaria/pj/feriasview.html', {'qs': qs,'dias':dias,'hoje':hoje})
            return render(request, 'portaria/pj/feriasview.html', {'qs': qs, 'dias': dias, 'hoje': hoje})


    return render(request, 'portaria/pj/feriasview.html', {'qs': qs,'dias':dias,'hoje':hoje})

def feriasagen(request, idfpj):
    form = feriaspjForm
    fer = get_object_or_404(feriaspj, pk=idfpj)
    agen1 = request.GET.get('agendamento1')
    agen2 = request.GET.get('agendamento2')
    if agen1 and agen2:
        try:
            agenparse1 = datetime.datetime.strptime(agen1, '%Y-%m-%d').date()
            agenparse2 = datetime.datetime.strptime(agen2, '%Y-%m-%d').date()
            feriaspj.objects.filter(pk=fer.id).update(agendamento_ini=agenparse1, agendamento_fim=agenparse2)
        except ValueError:
            messages.error(request, 'Por favor digite uma data válida')
            return render(request, 'portaria/pj/agendamento.html', {'fer':fer})
        else:
            messages.success(request, 'Agendamento feito com sucesso')
            return redirect('portaria:feriasview')
    return render(request, 'portaria/pj/agendamento.html', {'fer':fer,'form':form})

def feriasquit(request, idfpj):
    fer = get_object_or_404(feriaspj, pk=idfpj)
    try:
        feriaspj.objects.filter(pk=fer.id).update(quitado=True, dt_quitacao=timezone.now())
    except ObjectDoesNotExist:
        messages.error(request, 'Erro')
        return redirect('portaria:feriasview')
    else:
        messages.success(request, f'Férias quitadas para o funcionário {fer}')
        return redirect('portaria:feriasview')

def frotacadastros(request):
    return render(request, 'portaria/frota/frotacadastros.html')

def cadmotorista(request):
    form = MotoristaForm
    if request.method == 'POST':
        form = MotoristaForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastrado com sucesso')
            return redirect('portaria:frotacadastros')
    return render(request, 'portaria/frota/cadmotorista.html', {'form':form})

def cadveiculo(request):
    form = VeiculosForm
    if request.method == 'POST':
        form = VeiculosForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastrado com sucesso')
            return redirect('portaria:frotacadastros')
    return render(request, 'portaria/frota/cadveiculo.html', {'form': form})

def cadtpservico(request):
    form = TipoServicosManutForm
    if request.method == 'POST':
        form = TipoServicosManutForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastrado com sucesso')
            return redirect('portaria:frotacadastros')
    return render(request, 'portaria/frota/cadtpservico.html', {'form':form})

@login_required
def manutencaofrota(request):
    if request.method == 'GET':
        pla = request.GET.get('placa')
        if pla:
            try:
                Veiculos.objects.get(prefixoveic=pla)
            except ObjectDoesNotExist:
                messages.error(request, 'Veículo não encontrado')
                return render(request, 'portaria/manutencaofrota.html')
            else:
                return redirect('portaria:manuentrada', placa_id=pla)

    if request.method == 'POST':
        idmanu = request.POST.get('idmanu')
        try:
            ManutencaoFrota.objects.get(pk=idmanu)
        except ObjectDoesNotExist:
            messages.error(request, 'OS não encontrado')
            return render(request, 'portaria/manutencaofrota.html')
        except ValueError:
            messages.error(request, 'Por gentileza digite o OS corretamente')
            return render(request, 'portaria/frota/manutencaofrota.html')
        else:
            return redirect('portaria:manusaida', osid=idmanu)
    return render(request, 'portaria/frota/manutencaofrota.html')

def manupendentes(request):
    qs = ManutencaoFrota.objects.filter(status='PENDENTE').order_by('dt_entrada')
    qs2 = ServJoinManu.objects.all()
    if request.method == 'GET':
        placa = request.GET.get('isplaca')
        if placa:
            qs = ManutencaoFrota.objects.filter(status='PENDENTE', veiculo__prefixoveic=placa).order_by('dt_entrada')
    if request.method == 'POST':
        osid = request.POST.get('os')
        try:
            isos = get_object_or_404(ManutencaoFrota, pk=osid)
            ManutencaoFrota.objects.filter(pk=isos.id).update(status='CONCLUIDO', autor=request.user)
        except ObjectDoesNotExist:
            return redirect('portaria:manupendentes')
        else:
            messages.success(request, f'Confirmado conclusão da os {isos}')
            return redirect('portaria:manupendentes')
    return render(request,'portaria/frota/manutencaopendencia.html', {'qs':qs,'qs2':qs2})

@login_required
def manuentrada(request, placa_id):
    print('inicio')
    array = []
    gp_servs = TipoServicosManut.objects.values_list('grupo_servico', flat=True).distinct()
    for q in gp_servs:
        tp_servs = TipoServicosManut.objects.filter(grupo_servico=str(q))
        concat = [str(q), tp_servs]
        array.append(concat)
    placa = get_object_or_404(Veiculos, prefixoveic=placa_id)
    form = ManutencaoForm
    autor = request.user
    ult_manu = Veiculos.objects.filter(pk=placa.codigoveic).values_list('manutencaofrota__dt_saida', flat=True)\
        .order_by('-manutencaofrota__dt_saida').first()
    if ult_manu == None: ult_manu = timezone.now()
    if request.method == 'POST':
        count = request.POST.get('setcount')
        tp_sv = request.POST.get('tp_servico')

        form = ManutencaoForm(request.POST or None)
        if form.is_valid():
            manu = form.save(commit=False)
            manu.veiculo_id = placa.codigoveic
            manu.dt_ult_manutencao = ult_manu
            manu.dt_entrada = timezone.now()
            manu.status = 'ANDAMENTO'
            manu.autor = autor
            manu.tp_servico = tp_sv
            try:
                manu.save()
                ServJoinManu.objects.create(id_svs_id=tp_sv, autor=autor, id_os_id=manu.id)
                if count:
                    ncount = int(count)
                    if ncount > 0:
                        for c in range(0, ncount):
                            d = c + 1
                            variable = 'tp_servico' + str(d)
                            tp_sv = request.POST.get(variable)
                            print(tp_sv)
                            if tp_sv:
                                ServJoinManu.objects.create(id_svs_id=tp_sv,autor=autor,id_os_id=manu.id)
                            else:
                                continue
            except Exception as e:
                raise e
            messages.success(request, f'Cadastro de manutenção do veículo {placa} feito com sucesso!')
            return redirect('portaria:manutencaoprint', osid= manu.id)
    return render(request, 'portaria/frota/manuentrada.html', {'placa':placa,'form':form,'array':array})


@login_required
def manusaida(request, osid):
    get_os = get_object_or_404(ManutencaoFrota, pk=osid)
    if get_os.dt_saida == None:
        dtsaida = request.POST.get('dtsaida')
        vlmao = request.POST.get('vlmao')
        vlpeca = request.POST.get('vlpeca')
        if dtsaida:
            try:
                date_dtsaida = datetime.datetime.strptime(dtsaida, '%d/%m/%Y').date()
            except ValueError:
                messages.error(request, 'Por favor digite uma data válida')
                return render(request, 'portaria/frota/manusaida.html',{'get_os':get_os})
            else:
                between_days = (date_dtsaida - get_os.dt_entrada).days
                ManutencaoFrota.objects.filter(pk=get_os.id).update(valor_peca=vlpeca,valor_maodeobra=vlmao,
                                                                    dt_saida=date_dtsaida,
                                                                    dias_veic_parado=str(between_days),
                                                                    status='PENDENTE',
                                                                    autor=request.user)

                messages.success(request, f'Saída cadastrada para OS {get_os.id}, placa {get_os.veiculo}')
                return redirect('portaria:manutencaoview')
        return render(request, 'portaria/frota/manusaida.html',{'get_os':get_os})
    else:
        messages.error(request, 'Saída já cadastrada para OS')
        return redirect('portaria:manutencaofrota')

class ManutencaoListView(generic.ListView):
    template_name = 'portaria/frota/manutencaoview.html'
    context_object_name = 'lista'

    def get_queryset(self):
        qs = ManutencaoFrota.objects.filter(dt_saida=None,).order_by('dt_entrada')

        try:
            placa = self.request.GET.get('isplaca')
            if placa:
                qs = ManutencaoFrota.objects.filter(dt_saida=None, veiculo__prefixoveic=placa).order_by('dt_entrada')
        except ObjectDoesNotExist:
            raise Exception('Valor digitado inválido')
        return qs

    def get_context_data(self, **kwargs):
        data = ServJoinManu.objects.all()
        context = super().get_context_data(**kwargs)
        context['form'] = data
        return context


@login_required
def manutencaoprint(request, osid):
    os = get_object_or_404(ManutencaoFrota, pk=osid)
    aa = ServJoinManu.objects.filter(id_os=os.id).annotate(grp=F('id_svs__grupo_servico'), svs=F('id_svs__tipo_servico'))
    return render(request, 'portaria/frota/manutencaoprint.html', {'os':os,'aa':aa})

def fatferramentas(request):
    return render(request,'portaria/etc/fatferramentas.html')

def monitticket(request):
    employee = User.objects.filter(groups__name='monitoramento').exclude(id=1)
    tkts = TicketMonitoramento.objects.filter(Q(status='ABERTO') | Q(status='ANDAMENTO'))

    if request.method == 'POST':
        tkt = request.POST.get('srctkt')
        employee1 = request.POST.get('employee')
        period1 = request.POST.get('period1')
        period2 = request.POST.get('period2')
        stts = request.POST.getlist('stts_choice')

        if tkt:
            tkts = TicketMonitoramento.objects.filter(Q(pk=tkt)|Q(nome_tkt__icontains=tkt)).exclude(
                Q(status='CANCELADO')|Q(status='CONCLUIDO'))
        if employee1 and not period1 and not period2:
            tkts = TicketMonitoramento.objects.filter(responsavel_id=employee1, status__in=stts)
        elif period1 and period2 and not employee1:
            tkts = TicketMonitoramento.objects.filter(dt_abertura__lte=period2, dt_abertura__gte=period1, status__in=stts)
        elif period1 and period2 and employee1:
            tkts = TicketMonitoramento.objects.filter(dt_abertura__lte=period2, dt_abertura__gte=period1,
                                                      responsavel_id=employee1, status__in=stts)
        elif not period1 and not period2 and not employee1 and stts:
            messages.error(request, 'Por gentileza selecione o período ou o funcionário')
        return render(request, 'portaria/monitoramento/monitticket.html', {'tkts': tkts,'employee':employee})
    return render(request, 'portaria/monitoramento/monitticket.html', {'tkts':tkts,'employee':employee})

def tktcreate(request):
    users = User.objects.filter(groups__name='monitoramento').exclude(id=1)
    tp_doc_choices = TIPO_DOCTO_CHOICES
    editor = TextEditor()
    garagem = TicketMonitoramento.GARAGEM_CHOICES
    opts = TicketMonitoramento.CATEGORIA_CHOICES
    file = UploadForm
    if request.method == 'GET':
        cte = request.GET.get('cte')
        gar = request.GET.get('garagem')
        tp_docto = request.GET.get('tp_docto')
        if cte and gar and tp_docto:
            if tp_docto == '8':
                remet = 'BC.RSOCIALCLI'
                dest = 'F11.REC_RZ_SOCIAL'
            else:
                remet = 'F1.REM_RZ_SOCIAL'
                dest = 'F1.DEST_RZ_SOCIAL'
            try:
                conn = settings.CONNECTION
                cur = conn.cursor()
                cur.execute(f'''
                                SELECT 
                                      F1.EMPRESA,
                                      CASE
                                          WHEN F1.ID_EMPRESA = '1' AND F1.ID_GARAGEM = '1'  THEN 'SPO'
                                          WHEN F1.ID_EMPRESA = '1' AND F1.ID_GARAGEM = '2'  THEN 'REC'
                                          WHEN F1.ID_EMPRESA = '1' AND F1.ID_GARAGEM = '3'  THEN 'SSA'
                                          WHEN F1.ID_EMPRESA = '1' AND F1.ID_GARAGEM = '4'  THEN 'FOR'
                                          WHEN F1.ID_EMPRESA = '1' AND F1.ID_GARAGEM = '5'  THEN 'MCZ'
                                          WHEN F1.ID_EMPRESA = '1' AND F1.ID_GARAGEM = '6'  THEN 'NAT'
                                          WHEN F1.ID_EMPRESA = '1' AND F1.ID_GARAGEM = '7'  THEN 'JPA'
                                          WHEN F1.ID_EMPRESA = '1' AND F1.ID_GARAGEM = '8'  THEN 'AJU'
                                          WHEN F1.ID_EMPRESA = '1' AND F1.ID_GARAGEM = '9'  THEN 'VDC'
                                          WHEN F1.ID_EMPRESA = '1' AND F1.ID_GARAGEM = '10' THEN 'MG'
                                          WHEN F1.ID_EMPRESA = '1' AND F1.ID_GARAGEM = '50' THEN 'SPO'
                                          WHEN F1.ID_EMPRESA = '1' AND F1.ID_GARAGEM = '20' THEN 'SPO'
                                          WHEN F1.ID_EMPRESA = '1' AND F1.ID_GARAGEM = '21' THEN 'SPO'
                                          WHEN F1.ID_EMPRESA = '2' AND F1.ID_GARAGEM = '20' THEN 'CTG'
                                          WHEN F1.ID_EMPRESA = '2' AND F1.ID_GARAGEM = '21' THEN 'TCO'
                                          WHEN F1.ID_EMPRESA = '2' AND F1.ID_GARAGEM = '22' THEN 'UDI'
                                          WHEN F1.ID_EMPRESA = '2' AND F1.ID_GARAGEM = '23' THEN 'TMA'
                                          WHEN F1.ID_EMPRESA = '2' AND F1.ID_GARAGEM = '24' THEN 'VIX'  
                                          WHEN F1.ID_EMPRESA = '2' AND F1.ID_GARAGEM = '50' THEN 'VIX'
                                          WHEN F1.ID_EMPRESA = '3' AND F1.ID_GARAGEM = '30' THEN 'BMA'
                                          WHEN F1.ID_EMPRESA = '3' AND F1.ID_GARAGEM = '31' THEN 'BPE'
                                          WHEN F1.ID_EMPRESA = '3' AND F1.ID_GARAGEM = '32' THEN 'BEL'    
                                          WHEN F1.ID_EMPRESA = '3' AND F1.ID_GARAGEM = '33' THEN 'BPB'
                                          WHEN F1.ID_EMPRESA = '3' AND F1.ID_GARAGEM = '34' THEN 'SLZ'
                                          WHEN F1.ID_EMPRESA = '3' AND F1.ID_GARAGEM = '35' THEN 'BAL'
                                          WHEN F1.ID_EMPRESA = '3' AND F1.ID_GARAGEM = '36' THEN 'THE'  
                                      END GARAGEM,
                                      F1.DEST_MUNIC_DEST,
                                      F1.DEST_UF_DEST,
                                      F1.TIPO_DOCTO,
                                      F1.CONHECIMENTO CTE,
                                      {remet} REMETENTE,
                                      {dest} DESTINATARIO,
                                      LISTAGG ((LTRIM (F4.NOTA_FISCAL,0)), ' / ') WITHIN GROUP (ORDER BY F1.CONHECIMENTO) NOTA_FISCAL 
                                FROM
                                    FTA001 F1,
                                    FTA004 F4,
                                    FTA011 F11,
                                    BGM_CLIENTE BC
                                WHERE
                                     F1.EMPRESA = F4.EMPRESA AND
                                     F1.FILIAL = F4.FILIAL   AND
                                     F1.GARAGEM = F4.GARAGEM AND
                                     F1.CONHECIMENTO = F4.CONHECIMENTO AND
                                     F1.SERIE = F4.SERIE               AND
                                     F1.TIPO_DOCTO = F4.TIPO_DOCTO     AND
                                     F1.EMPRESA = F11.EMPRESA           AND
                                     F1.FILIAL = F11.FILIAL             AND
                                     F1.GARAGEM = F11.GARAGEM           AND
                                     F1.CONHECIMENTO = F11.CONHECIMENTO AND
                                     F1.SERIE = F11.SERIE               AND
                                     F1.TIPO_DOCTO = F11.TIPO_DOCTO     AND
                                     F1.CONHECIMENTO = {cte}           AND
                                     F1.GARAGEM = {gar}             AND
                                     F1.TIPO_DOCTO = {tp_docto}        AND
                                     F1.DATA_EMISSAO BETWEEN ((SYSDATE) - 90) AND (SYSDATE) AND
                                     F1.CLIENTE_FAT = BC.CODCLI                                                      
                                GROUP BY
                                     F1.EMPRESA,
                                     F1.ID_EMPRESA,
                                     F1.ID_GARAGEM,
                                     F1.TIPO_DOCTO,
                                     F1.CONHECIMENTO,
                                     F1.REM_RZ_SOCIAL,
                                     F1.DEST_RZ_SOCIAL,
                                     F1.DEST_MUNIC_DEST,
                                     F1.DEST_UF_DEST,
                                     BC.RSOCIALCLI,
                                     F11.REC_RZ_SOCIAL''')
                res = dictfetchall(cur)
            except Exception as e:
                messages.error(request, f'{e}')
                return redirect('portaria:monitticket')
            else:
                if len(res)>1:
                    messages.error(request, f'Mais de 1 registro encontrado')
                    return redirect('portaria:monitticket')
                elif res:
                    modal = EmailOcorenciasMonit.objects.filter(rsocial=res[0]['REMETENTE'], ativo=1)
                    return render(request, 'portaria/monitoramento/tktcreate.html', {'editor': editor, 'users': users,
                                                                 'res': res,'opts': opts,'file':file, 'modal':modal})
                else:
                    messages.error(request, f'Nenhum registro encontrado')
                    return redirect('portaria:monitticket')
    if request.method == 'POST':
        responsavel = request.POST.get('responsavel')
        cte = request.POST.get('cte')
        tp_docto = request.POST.get('tp_docto')
        assunto = request.POST.get('assunto')
        cc = request.POST.get('cc').replace(',', ';')
        filial = request.POST.get('filial')
        mensagem = request.POST.get('area')
        rem = request.POST.get('remetente')
        dest = request.POST.get('destinatario')
        if request.POST.get('file') != '':
            myfile = request.FILES.getlist('file')
        else:
            myfile = None
        if responsavel and rem and mensagem and assunto and cc and dest:
            if TicketMonitoramento.objects.filter(nome_tkt=assunto).exists():
                assunto += '*'
                createtktandmail(request, **{'resp':responsavel,'cc':cc, 'rem':rem, 'filial':filial, 'dest':dest,
                                               'assunto':assunto, 'msg':mensagem, 'cte':cte, 'tp_docto':tp_docto,
                                               'file':myfile})
            else:
                createtktandmail(request, **{'resp':responsavel, 'cc':cc, 'rem':rem, 'filial':filial, 'dest':dest,
                                             'assunto':assunto, 'msg':mensagem, 'cte':cte, 'tp_docto':tp_docto,
                                             'file':myfile})
        else:
            messages.error(request, 'Está faltando campos')
        return redirect('portaria:monitticket')

    return render(request, 'portaria/monitoramento/tktcreate.html',{'editor': editor, 'users': users, 'opts': opts,
                                                                    'tp_doc_choices':tp_doc_choices, 'garagem':garagem})

def modaltkt(request):
    ccs = request.POST.getlist('vals[]')
    for q in ccs:
        try:
            EmailOcorenciasMonit.objects.filter(email=q).update(ativo=0)
        except Exception as e:
            print(e)
        else:
            print('200')
    return HttpResponse('200')

def tktview(request, tktid):
    opts = TicketMonitoramento.CATEGORIA_CHOICES
    stts = TicketMonitoramento.STATUS_CHOICES
    form = get_object_or_404(EmailMonitoramento, tkt_ref_id=tktid)
    teste = []
    try:
        for q in form.ult_resp_html.split('<p>Anterior</p><hr>'):
            teste.append(q)
    except:
        pass
    editor = TextEditor()
    file = UploadForm
    keyga = {v:k for k, v in TicketMonitoramento.GARAGEM_CHOICES}
    if request.method == 'POST':
        ctg = request.POST.get('categs')
        addcc = request.POST.get('addcc')
        nstts = request.POST.get('stts')
        if ctg != 'selected':
            TicketMonitoramento.objects.filter(pk=tktid).update(categoria=ctg)

        if nstts != 'selected':
            tkt = get_object_or_404(TicketMonitoramento, pk=tktid)
            if tkt and tkt.categoria != 'Aguardando Recebimento':
                TicketMonitoramento.objects.filter(pk=tkt.id).update(status=nstts)
                messages.info(request, f'Ticket {tkt.id} alterado para {nstts} com sucesso.')
            else:
                messages.error(request, f'Não autorizado a mudança de status para {nstts}, por gentileza mude a primeira categoria.')
                return redirect('portaria:monitticket')

        if addcc:
            oldcc = form.cc
            newcc = oldcc + addcc+','

            try:
                EmailMonitoramento.objects.filter(tkt_ref_id=tktid).update(cc=newcc)
            except Exception as e:
                print(e)

        area = request.POST.get('area')
        if area and area != '<p><br></p>':
            if request.POST.get('file') != '':
                myfile = request.FILES.getlist('file')
            else:
                myfile = None
            replymail_monitoramento(request, tktid, area, myfile)
        return redirect('portaria:monitticket')
    return render(request, 'portaria/monitoramento/ticketview.html', {'form':form,'editor':editor,'opts':opts,
                                                                      'stts':stts,'teste':teste})

def tktmetrics(request):
    hj = datetime.date.today()
    metrics = TicketMonitoramento.objects.exclude(status='CANCELADO').annotate(
        total=Count('id', filter=~Q(status='CONCLUIDO')), hoje=Count('id', filter=Q(dt_abertura=hj)),
        andamento=Count('id', filter=Q(status='ANDAMENTO')), aberto=Count('id', filter=Q(status='ABERTO'))
    ).aggregate(total1=Sum('total'), hoje1=Sum('hoje'), andamento1=Sum('andamento'), aberto1=Sum('aberto'))

    totfunc = User.objects.filter(groups=9)\
        .annotate(total=Count('responsavel__id',filter=Q(responsavel__dt_abertura__month=datetime.datetime.now().month,
                                                         responsavel__dt_abertura__year=datetime.datetime.now().year)),
                 diario=Count('responsavel__id',filter=Q(responsavel__dt_abertura=datetime.date.today())),
                 concluido=Count('responsavel__id',filter=Q(responsavel__dt_abertura__month=datetime.datetime.now().month,
                                                            responsavel__dt_abertura__year=datetime.datetime.now().year,
                                                            responsavel__status='CONCLUIDO')))

    return render(request, 'portaria/monitoramento/ticketmetrics.html', {'metrics':metrics,'totfunc':totfunc})

def chamado(request):
    metrics = TicketChamado.objects.exclude(Q(status='CANCELADO') | Q(status='CONCLUIDO')).annotate(
        dev=Count('id', filter=Q(servico='DESENVOLVIMENTO')), praxio=Count('id', filter=Q(servico='PRAXIO')),
        ti=Count('id', filter=Q(servico='TI')), manutencao=Count('id', filter=Q(servico='MANUTENCAO'))
    ).aggregate(dev1=Sum('dev'), praxio1=Sum('praxio'), ti1=Sum('ti'), manu1=Sum('manutencao'))
    return render(request, 'portaria/chamado/chamado.html', {'metrics':metrics})

def chamadopainel(request):
    groups = request.user.groups.values_list('name', flat=True)
    form = TicketChamado.objects.filter(servico__in=groups
    ).exclude(Q(status='CANCELADO') | Q(status='CONCLUIDO'))

    if request.method == 'POST':
        srctkt = request.POST.get('srctkt')
        if srctkt:
            form = TicketChamado.objects.filter(pk=srctkt).exclude(Q(status='CANCELADO') | Q(status='CONCLUIDO'))
            return render(request, 'portaria/chamado/chamadopainel.html', {'form': form})
    return render(request, 'portaria/chamado/chamadopainel.html',{'form':form})

def chamadonovo(request):
    editor = TextEditor()
    stts = TicketChamado.STATUS_CHOICES
    dp = TicketChamado.DEPARTAMENTO_CHOICES
    fil = TIPO_GARAGEM
    svs = TicketChamado.SERVICO_CHOICES
    resp = User.objects.filter(groups__name='chamado').exclude(id=1)
    if request.method == 'POST':
        assnt = request.POST.get('assunto')
        solic = request.POST.get('solicitante')
        nresp = request.POST.get('responsavel')
        ndp = request.POST.get('departamento')
        nstts = request.POST.get('status')
        nfil = request.POST.get('filial')
        nsvs = request.POST.get('svs')
        area = request.POST.get('area')
        if assnt and solic and nresp and ndp and nstts and nfil and area and area != '<p><br></p>':
            dict = {
                'assnt':assnt,
                'solic': solic,
                'nresp': nresp,
                'ndp': ndp,
                'nstts': nstts,
                'nfil': nfil,
                'area':area,
                'nsvs': nsvs
            }
            createchamado(request, **dict)
    return render(request, 'portaria/chamado/chamadonovo.html', {'editor':editor,'stts':stts,'dp':dp,'fil':fil,
                                                                 'resp':resp,'svs':svs})


def chamadodetail(request, tktid):
    stts = TicketChamado.STATUS_CHOICES
    dp = TicketChamado.DEPARTAMENTO_CHOICES
    fil = TIPO_GARAGEM
    resp = User.objects.filter(groups__name='chamado').exclude(id=1)
    form = get_object_or_404(EmailChamado, tkt_ref=tktid)
    editor = TextEditor()

    if request.method == 'POST':
        ndptm = request.POST.get('ndptm')
        nstts = request.POST.get('nstts')
        nresp = request.POST.get('nresp')
        nfil = request.POST.get('nfil')
        area = request.POST.get('area')

        try:
            if ndptm != 'selected':
                TicketChamado.objects.filter(pk=form.tkt_ref_id).update(departamento=ndptm)
            if nresp != 'selected':
                TicketChamado.objects.filter(pk=form.tkt_ref_id).update(responsavel=nresp)
            if nfil != 'selected':
                TicketChamado.objects.filter(pk=form.tkt_ref_id).update(filial=nfil)
            if nstts != 'selected':
                if nstts == 'CONCLUIDO' or nstts == 'CANCELADO':
                    if form.tkt_ref.status == 'ABERTO':
                        messages.error(request, 'Não autorizado encerramento do monitoramento.')
                        return redirect('portaria:chamado')
                    else:
                        TicketChamado.objects.filter(pk=form.tkt_ref_id).update(status=nstts)
                else:
                    TicketChamado.objects.filter(pk=form.tkt_ref_id).update(status=nstts)
            if area and area != '<p><br></p>':
                chamadoupdate(request, tktid, area)
        except Exception as e:
            print(e)
    return render(request, 'portaria/chamado/chamadodetail.html', {'form':form,'editor':editor,'stts':stts,'dp':dp,
                                                                   'resp':resp,'fil':fil})
#fim das views


#funcoes variadas
@login_required
def transfpalete(request):
    form = TPaletesForm()
    if request.method == 'POST':
        ori = request.POST.get('origem_')
        des = request.POST.get('destino_')
        qnt = int(request.POST.get('quantidade_'))
        plc = request.POST.get('placa_veic')
        tp_p = request.POST.get('tp_palete')
        if qnt <= PaleteControl.objects.filter(loc_atual=ori,tp_palete=tp_p).count():
            print(ori,des,qnt,plc,tp_p)
            for q in range(0,qnt):
                x = PaleteControl.objects.filter(loc_atual=ori, tp_palete=tp_p).first()
                MovPalete.objects.create(palete=x,data_ult_mov=timezone.now(),origem=ori,destino=des, placa_veic=plc,
                                         autor=request.user)
                PaleteControl.objects.filter(pk=x.id).update(loc_atual=des)
            messages.success(request, f'{qnt} palete transferido de {ori} para {des}')
            return render(request,'portaria/palete/transfpaletes.html', {'form':form})
        else:
            messages.error(request,'Quantidade solicitada maior que a disponível')
            return render(request,'portaria/palete/transfpaletes.html', {'form':form})

    return render(request,'portaria/palete/transfpaletes.html', {'form':form})



@login_required
def get_nfpj_mail(request):
    a = request.POST.get('total')
    b = request.POST.get('adiantamento')
    dt_1 = request.POST.get('periodo1')
    dt_2 = request.POST.get('periodo2')
    dt_pgmt = request.POST.get('dt_pgmt')
    text = ""
    title = ''
    if a:
        title = 'NF'
        qs = FuncPj.objects.filter(ativo=True)
        text = '''
                Favor emitir a nf. de prestação serviços
                Período de: {16} a {17}
                Valor do Serviço: R$ {2:.2f}
                Prêmios: R$ {6:.2f}
                Ajuda de custo: R$ {4:.2f}
                Forma de Pagamento: R$ {10:.2f}
                Data de pagamento {18}
                Serviço Prestado no {0}
                Dados Bancários: Banco {12} Ag. {13} C.c. {14}
                CPF: {11}
                '''
    if b:
        title = 'NF ADIANTAMENTO'
        qs = FuncPj.objects.filter(ativo=True, adiantamento__gt=0)
        text = """ 
                Prestação de Serviços 
                Período de: {16} até {17}
                Valor do Serviço: R$ {7:.2f}
                Forma de Pagamento: R$ {7:.2f}
                Data de pagamento:  {18}
                Serviço Prestado em {0}
                Dados Bancários: Banco {12} Ag. {13} C.c. {14}
                CPF: {11}
                Favor enviar a nf até {18}.
                Att
                """
    arrya = []
    for q in qs:
        query = FuncPj.objects.filter(pk=q.id) \
            .annotate(
             faculdade=Coalesce(Sum('nfservicopj__faculdade',filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
             cred_convenio=Coalesce(Sum('nfservicopj__cred_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
             outros_cred=Coalesce(Sum('nfservicopj__outros_cred', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
             desc_convenio=Coalesce(Sum('nfservicopj__desc_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
             outros_desc=Coalesce(Sum('nfservicopj__outros_desc',filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
             ).annotate(total=(F('salario') + F('ajuda_custo') + F('faculdade') + F('cred_convenio') + F('outros_cred') ) - (F('adiantamento') + F('desc_convenio') + F('outros_desc')))
        arrya.extend(query)
    for q in arrya:
        try:
            send_mail(
                subject=title,
                message=text.format(
                    q.filial, q.nome, q.salario, q.faculdade, q.ajuda_custo, q.cred_convenio,
                    q.outros_cred, q.adiantamento, q.desc_convenio, q.outros_desc, q.total,
                    q.cpf_cnpj, q.banco, q.ag, q.conta, q.op, dt_1, dt_2, dt_pgmt,
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[q.email]
            )
            MailsPJ.objects.create(funcionario_id=q.id, data_pagamento=datetime.datetime.strptime(dt_pgmt,'%Y-%m-%d'),
                                   mensagem=text.format(
                    q.filial, q.nome, q.salario, q.faculdade, q.ajuda_custo, q.cred_convenio,
                    q.outros_cred, q.adiantamento, q.desc_convenio, q.outros_desc, q.total,
                    q.cpf_cnpj, q.banco, q.ag, q.conta, q.op, dt_1, dt_2, dt_pgmt,
                ))
        except Exception as e:
            print(e)
    return redirect('portaria:index')

def get_pj13_mail(request):
    getperiod = request.POST.get('period')
    array = []
    if getperiod == 'pgto_parcela_1':
        allfuncs = FuncPj.objects.filter(ativo=True, pj13__pgto_parc_1__isnull=False, pj13__pgto_parc_2__isnull=True)
        for q in allfuncs:
            query = FuncPj.objects.filter(pk=q.id).annotate(valor=F('pj13__valor'),
                                                            parc_1=F('pj13__pgto_parc_1'),
                                                            parc_2=F('pj13__pgto_parc_2'),
                                                            periodo=F('pj13__periodo_meses'))
            array.extend(query)
    elif getperiod == 'pgto_parcela_2':
        allfuncs = FuncPj.objects.filter(ativo=True, pj13__pgto_parc_2__isnull=False)
        for q in allfuncs:
            query = FuncPj.objects.filter(pk=q.id).annotate(valor=F('pj13__valor'),
                                                            parc_1=F('pj13__pgto_parc_1'),
                                                            parc_2=F('pj13__pgto_parc_2'),
                                                            periodo=F('pj13__periodo_meses'))
            array.extend(query)
    for q in array:
        send_mail(
            subject='Pagamento Bonificação 13º',
            message=f'''
                                Unidade: {q.filial}
                                Nome: {q.nome}
                                Cpf: {q.cpf_cnpj}
                                Salario: {q.salario:.2f}
                                1ª Parcela: {q.valor:.2f}
                                2ª Parcela: {q.valor:.2f}
                            ''',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[q.email]
        )
    messages.success(request, f'Emails enviados para {len(array)} funcionarios')
    return redirect('portaria:decimopj')

def get_pj13_csv(request):
    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition': 'attachment; filename="pjdecimo.csv"'})
    writer = csv.writer(response)
    writer.writerow(['id', 'periodo_meses', 'valor', 'pgto_parc_1', 'pgto_parc_2', 'funcionario', 'autor'])
    pj = pj13.objects.all().values_list(
        'id', 'periodo_meses', 'valor', 'pgto_parc_1', 'pgto_parc_2', 'funcionario__nome', 'autor__username'
    )
    for id in pj:
        writer.writerow(id)
    return response

def get_portaria_csv(request):
    data1 = request.POST.get('dataIni')
    data2 = request.POST.get('dataFim')
    fil = request.POST.get('filial')
    if fil and not data1 and not data2:
        cadastro = Cadastro.objects.all().annotate(
            hr_chegada_fmt=Cast(TruncMinute('hr_chegada', DateTimeField()), CharField()),hr_saida_fmt=Cast(TruncMinute('hr_chegada', DateTimeField()), CharField())) \
            .values_list('placa', 'placa2', 'motorista', 'empresa', 'origem', 'destino','tipo_mot', 'tipo_viagem', 'hr_chegada_fmt', 'hr_saida_fmt', 'autor__username')\
            .filter(origem=fil)
    elif data1 and data2 and not fil:
        dateparse = datetime.datetime.strptime(data1, '%Y-%m-%d').replace(hour=00, minute=00)
        dateparse1 = datetime.datetime.strptime(data2, '%Y-%m-%d').replace(hour=23, minute=59)
        cadastro = Cadastro.objects.all().annotate(
            hr_chegada_fmt=Cast(TruncMinute('hr_chegada', DateTimeField()), CharField()),
            hr_saida_fmt=Cast(TruncMinute('hr_chegada', DateTimeField()), CharField())) \
            .values_list('placa', 'placa2', 'motorista', 'empresa', 'origem', 'destino', 'tipo_mot', 'tipo_viagem',
                         'hr_chegada_fmt', 'hr_saida_fmt', 'autor__username') \
            .filter(hr_chegada__gte=dateparse, hr_chegada__lte=dateparse1)
    else:
        dateparse = datetime.datetime.strptime(data1, '%Y-%m-%d').replace(hour=00, minute=00)
        dateparse1 = datetime.datetime.strptime(data2, '%Y-%m-%d').replace(hour=23, minute=59)
        cadastro = Cadastro.objects.all().annotate(
            hr_chegada_fmt=Cast(TruncMinute('hr_chegada', DateTimeField()), CharField()),
            hr_saida_fmt=Cast(TruncMinute('hr_chegada', DateTimeField()), CharField())) \
            .values_list('placa', 'placa2', 'motorista', 'empresa', 'origem', 'destino', 'tipo_mot', 'tipo_viagem',
                         'hr_chegada_fmt', 'hr_saida_fmt', 'autor__username') \
            .filter(hr_chegada__gte=dateparse, hr_chegada__lte=dateparse1, origem=fil)

    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition': 'attachment; filename="portaria.csv"'},
                            )

    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(['Placa','Placa2','Motorista','Empresa','Origem','Destino','Tipo_mot','Tipo_viagem',
                     'Hr_entrada','Hr_Saida','autor'])

    for placa in cadastro:
        writer.writerow(placa)
    return response

def get_palete_csv(request):
    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition':'attachment; filename="paletes.csv"'})
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(['id','loc_atual','empresa','ultima_viagem','origem','destino','placa_veic','autor'])
    palete = PaleteControl.objects.all().values_list(
        'id', 'loc_atual', 'empresa__razao_social','movpalete__data_ult_mov', 'movpalete__origem', 'movpalete__destino', 'movpalete__placa_veic','movpalete__autor__username'
    )
    for id in palete:
        writer.writerow(id)
    return response

def get_manu_csv(request):
    try:
        data1 = request.POST.get('dataIni')
        data2 = request.POST.get('dataFin')
        dateparse = datetime.datetime.strptime(data1, '%Y-%m-%d')
        dateparse1 = datetime.datetime.strptime(data2, '%Y-%m-%d')
    except ValueError:
        messages.error(request,'Por favor digite uma data válida')
        return redirect('portaria:manutencaofrota')
    else:
        response = HttpResponse(content_type='text/csv',
                                headers={'Content-Disposition':f'attatchment; filename="manutencao{dateparse}-{dateparse1}.csv"'})
        response.write(u'\ufeff'.encode('utf8'))
        writer = csv.writer(response)
        writer.writerow(['id','veiculo','tp_manutencao','local_manu','dt_ult_manutencao','dt_entrada','dt_saida',
                            'dias_veic_parado','km_ult_troca_oleo','tp_servico','valor_maodeobra','valor_peca',
                                'filial','socorro','prev_entrega','observacao','status','autor'])
        manutencao = ManutencaoFrota.objects.all().values_list('id','veiculo__prefixoveic','tp_manutencao','local_manu','dt_ult_manutencao','dt_entrada','dt_saida',
                            'dias_veic_parado','km_ult_troca_oleo','servjoinmanu__id_svs','valor_maodeobra','valor_peca',
                                'filial','socorro','prev_entrega','observacao','status','autor__username').filter(dt_entrada__gte=dateparse, dt_entrada__lte=dateparse1)
        for id in manutencao:
            writer.writerow(id)
        return response

def mailferias(request,idfpj):
    fer = get_object_or_404(feriaspj, pk=idfpj)
    func = get_object_or_404(FuncPj, pk=fer.funcionario_id)
    valor = 0
    if fer.tp_pgto == 'INTEGRAL':
        valor = fer.valor_integral
    else:
        valor = fer.valor_parcial1 + fer.valor_parcial2
    try:
        send_mail(
            subject='Informações Férias',
            message=f'''
                                        Unidade: {func.filial}
                                        Nome: {func.nome}
                                        Cpf: {func.cpf_cnpj}
                                        Início Férias: {fer.ultimas_ferias_ini}
                                        Fim Férias: {fer.ultimas_ferias_fim}
                                        Período  dias: {fer.periodo}
                                        Tipo Pgto: {fer.tp_pgto}
                                        Valor a receber: {valor}
                                    ''',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[func.email]
        )

    except ValueError:
        messages.error(request, 'Erro')
        return redirect('portaria:feriasview')
    else:
        messages.success(request, f'Email enviado para {func}')
        return redirect('portaria:feriasview')


def get_nfpj_csv(request):
    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition':'attatchment; filename="servicospj.csv"'})
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(['nome','cpf/cnpj','salario','ajuda de custo','adiantamento','credito convenio','outros creditos',
                     'desconto convenio','outros descontos','total a pagar'])
    arrya = []
    qnt_funcs = FuncPj.objects.filter(ativo=True)
    for q in qnt_funcs:
        query = FuncPj.objects.filter(pk=q.id) \
            .annotate(
            faculdade=Coalesce(Sum('nfservicopj__faculdade', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
            cred_convenio=Coalesce(Sum('nfservicopj__cred_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
            outros_cred=Coalesce(Sum('nfservicopj__outros_cred', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
            desc_convenio=Coalesce(Sum('nfservicopj__desc_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
            outros_desc=Coalesce(Sum('nfservicopj__outros_desc', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),) \
            .annotate(total=((F('salario') + F('ajuda_custo') + F('faculdade') + F('cred_convenio') + F('outros_cred')) - (F('adiantamento') + F('desc_convenio') + F('outros_desc'))))
        arrya.extend(query)
    for q in arrya:
        writer.writerow([q.nome,q.cpf_cnpj,q.salario,q.faculdade,q.cred_convenio,q.outros_cred,q.outros_cred,q.desc_convenio,q.outros_desc,q.total])
    return response

def get_checklist_csv(request):
    try:
        ini = datetime.datetime.strptime(request.POST.get('dataini'), '%Y-%m-%d').date()
        fim = datetime.datetime.strptime(request.POST.get('datafim'), '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Por favor digite uma data válida')
        return redirect('portaria:frota')
    else:
        response = HttpResponse(content_type='text/csv',
                                headers={'Content-Disposition':'attachment; filename="servicospj.csv"'})
        response.write(u'\ufeff'.encode('utf8'))
        writer = csv.writer(response)
        writer.writerow(['data','placa','motorista','placa carreta','km anterior','km atual','horimetro','uniforme da empresa',
                         'motorista identificado por crachá','lanterna do farol dianteiro funcionando?','farol baixo funcionando?',
                         'farol alto funcionando?','lanterna direita funcionando?','lanterna esquerda funcionando?','lanternas traseiras funcionando?',
                         'luz de ré funcionando?','retrovisores estão em perfeito estado?','água no radiador está no nível','óleo de freio está no nível',
                         'óleo de motor está no nivel?','verificado todas as luzes de advertências?','verificado o freio de emergência?','verificado o alarme sonoro da ré?',
                         'verificado se existe vazamentos de óleo de motor?','verificado se existe vazamento de ar','verificado se existe vazamento de óleo hidráulico?',
                         'verificado se existe vazamento de água no radiador?','verificado se as mangueiras estão em condições boas?',
                         'pneus em boas condições?','as lonas de freio estão em boas condições?','os estepes estão bons?','a suspensão está em condições perfeitas?',
                         'o carro está limpo e higienizado?','foi verificado as luzes de advertência das laterais?','foi verificado o lacre da placa?',
                         'foi verificado se o aparelho thermoking apresenta falhas?','foi verificado a carroceria assoalho e bau?',
                         'foi verificado a luz de freio?','foi verificado a luz de ré?','foi verificado se as luzes da lanterna traseira direita funciona?',
                         'foi verificado se as luzes da lanterna traseira esquerda funciona','autor'])
        checklist = ChecklistFrota.objects.all().values_list('datachecklist','placaveic','motoristaveic','placacarreta','kmanterior','kmatual','horimetro','p1_1','p1_2','p2_1','p2_2','p2_3','p2_4','p2_5','p2_6','p2_7',
                                                            'p2_8','p2_9','p2_10','p2_11','p2_12','p2_13','p2_14','p2_15','p2_16','p2_17','p2_18','p2_19','p2_20','p2_21','p2_22','p2_23','p2_24','p3_1',
                                                            'p3_2','p3_3','p3_4','p3_5','p3_6','p3_7','p3_8','obs','autor__username').filter(datachecklist__gte=ini,datachecklist__lte=fim)
        for c in checklist:
            writer.writerow(c)
        return response

def get_ferias_csv(request):
    try:
        ini = datetime.datetime.strptime(request.POST.get('dataini'), '%Y-%m-%d').date()
        fim = datetime.datetime.strptime(request.POST.get('datafim'), '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Por favor digite uma data válida')
        return redirect('portaria:feriaspjv')
    else:
        response = HttpResponse(content_type='text/csv',
                                headers={'Content-Disposition':'attatchment; filename="ferias.csv"'})
        response.write(u'\ufeff'.encode('utf8'))
        writer = csv.writer(response)
        writer.writerow(['ultimas ferias inicio','ultimas ferias fim','periodo','quitado','funcionario','vencimento','tipo pagamento',
                         'agendamento inicio','agendamento fim','valor integral','valor parcial 1', 'valor parcial 2','data quitacao','alerta vencimento'])
        ferias = feriaspj.objects.all().values_list('ultimas_ferias_ini','ultimas_ferias_fim','periodo','quitado','funcionario__nome','vencimento',
                                                    'tp_pgto','agendamento_ini','agendamento_fim','valor_integral','valor_parcial1','valor_parcial2',
                                                    'dt_quitacao','alerta_venc_enviado').filter(ultimas_ferias_ini__gte=ini,ultimas_ferias_fim__lte=fim)
        for q in ferias:
            writer.writerow(q)
        return response

def ediexceltosd1(request):
    array = []
    if request.method == 'POST':
        get_xlsx = request.FILES['edi_excel']
        response = HttpResponse(content_type='text/plain',
                                headers={'Content-Disposition': 'attatchment; filename="teste.sd1"'})
        if get_xlsx:
            edi = pd.read_excel(get_xlsx)
            for i,row in edi.iterrows():
                array.append(row)
            for q in range(len(array)):
                response.write(str(array[q]['tipo_de_registro']))
                response.write('    ')
                response.write('000000000000000')
                response.write(textwrap.wrap(array[q]['nome_do_cliente'], 40)[0].ljust(40,' '))
                response.write(str(array[q]['data_geracao']))
                response.write(str(array[q]['qtde_de_registro']))
                response.write('000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000')
                response.write(str(array[q]['numero_sec_arq']))
                response.write(str(array[q]['numero_sec_reg']))
                response.write('\n')
                response.write(str(array[q]['tipo_de_registro2']))
                response.write('    ')
                response.write('        ')
                response.write('  ')
                response.write('         ')
                response.write(str(array[q]['pais_de_origem']))
                response.write(str(array[q]['codigo_da_operacao']))
                response.write(str(array[q]['conteudo']))
                response.write(textwrap.wrap(str(array[q]['nome_dest']), 40)[0].ljust(40,' '))
                response.write(textwrap.wrap(str(array[q]['end_dest']), 40)[0].ljust(40,' '))
                response.write(textwrap.wrap(str(array[q]['cidade']), 30)[0].ljust(30,' '))
                response.write(str(array[q]['uf']))
                response.write(str(array[q]['cep']))
                response.write('00000000')
                response.write(str(array[q]['num_seq_arq2']))
                response.write(str(array[q]['num_seq_reg2']))
                response.write('\n')
        return response

def exedicorreios(request):
    response = HttpResponse(content_type='application/vnd.ms-excel',
                            headers={'Content-Disposition':'attatchment; filename="exemplo.xls"'})
    writer = csv.writer(response)
    writer.writerow(['tipo_de_registro','nome_do_cliente', 'data_geracao', 'qtde_de_registro', 'numero_sec_arq', 'numero_sec_reg','tipo_de_registro2','pais_de_origem','codigo_da_operacao','conteudo','nome_dest','end_dest','cidade','uf','cep','num_seq_arq2','num_seq_reg2'])
    writer.writerow(['8','exemplo da silva', 'aaaa/mm/dd','qnt registro do arquivo','numero sec arq','numero sec reg','9','BR','1234','conteudo','destinatario','endereco','cidade','uf','cep','num_seq_arq2','num_seq_reg2'])
    return response

def readmail_monitoramento(request):
    #params
    hoje = datetime.date.today()
    host = 'pop.kinghost.net' ########## alterar
    e_user = 'bora@bora.tec.br' ########## alterar
    e_pass = 'Bor@dev#123' ########## alterar
    pattern1 = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp)')
    pattern2 = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp).\w+.\w+')

    #logando no email
    pp = poplib.POP3(host)
    pp.set_debuglevel(1)
    pp.user(e_user)
    pp.pass_(e_pass)

    num_messages = len(pp.list()[1]) #conta quantos emails existem na caixa
    for i in range(num_messages):
        attatch = ''
        rr = random.random()
        #acessa o poplib e pega os emails
        try:
            raw_email = b'\n'.join(pp.retr(i+1)[1])
            parsed_email = email.message_from_bytes(raw_email, policy=policy.compat32)
        except Exception as e:
            print(f'parsed -- ErrorType: {type(e).__name__}, Error: {e}')
        else:
            if parsed_email.is_multipart():
                for part in parsed_email.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get('Content-Type'))
                    if ctype == 'text/plain' and 'attatchment' not in cdispo:
                        body = part.get_payload(decode=True)
                    elif ctype == 'text/html' and 'attatchment' not in cdispo:
                        body = part.get_payload(decode=True)
                        htbody = body

                    #verifica se existem arquivos no email
                    filename = part.get_filename()
                    if filename:
                        path = settings.STATIC_ROOT+'/monitoramento/'+str(hoje)+'/'
                        locimg = os.path.join(path, filename)
                        if os.path.exists(os.path.join(path)):
                            fp = open(locimg, 'wb')
                            fp.write(part.get_payload(decode=True))
                            fp.close()
                            os.chmod(locimg, 0o777)
                            try:
                                os.rename(locimg, os.path.join(path, (str(rr) + filename)))
                            except Exception as e:
                                os.rename(locimg, os.path.join(path, (str(rr) + filename + str(random.randint(1,100)))))
                        else:
                            os.mkdir(path=path)
                            os.chmod(path, 0o777)
                            fp = open(locimg, 'wb')
                            fp.write(part.get_payload(decode=True))
                            fp.close()
                            os.chmod(locimg, 0o777)
                            try:
                                os.rename(locimg, os.path.join(path, (str(rr) + filename)))
                            except Exception as e:
                                os.rename(locimg, os.path.join(path, (str(rr) + filename + str(random.randint(1,100)))))
                        item = os.path.join('/static/monitoramento/'+str(hoje)+'/', (str(rr) + filename))
                        aa = '<div class="mailattatch"><a href="'+item+'" download><img src="/static/images/downicon.png" width="40"><p>'+filename+'</p></a></div>'
                        attatch += aa
            else:
                body = parsed_email.get_payload(decode=True)
                htbody = body

            #pega decode do email
            cs = parsed_email.get_charsets()
            for q in cs:
                if q is None: continue
                else: cs = q

            #pega parametros do email
            try:
                e_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                e_title_unencoded = decode_header(parsed_email['Subject'])
                try:
                    e_title = e_title_unencoded[0][0].decode(cs)
                except:
                    e_title = parsed_email['Subject']

                e_from = parsed_email['From']
                if re.findall(r'<(.*?)>', e_from): e_from = re.findall(r'<(.*?)>', e_from)[0]

                e_to = parsed_email['To']
                if re.findall(r'<(.*?)>', e_to): e_to = re.findall(r'<(.*?)>', e_to)[0]
                e_cc = parsed_email['CC']
                if e_cc:
                    try:
                        e_cc = e_cc.split(',')
                        x = ''
                    except:
                        pass
                    else:
                        for q in e_cc:
                            if re.findall(r'<(.*?)>', q):
                                ncc = re.findall(r'<(.*?)>', q)
                                for a in ncc:
                                    x += a + ', '
                    e_cc = x
                e_id = parsed_email['Message-ID']
                e_ref = parsed_email['References']

                if e_ref is None: e_ref = e_id
                else:
                    e_ref = e_ref.split(' ')[0]
                    if len(e_ref[0]) == 1:
                        e_ref = e_ref.split(',')[0]
                #separa conteudo e pega attach
                e_body = body.decode(cs)
                w_body = '<div class="container chmdimg">' + htbody.decode(cs) + '</div>'
                if re.findall(pattern2,w_body):
                    for q in re.findall(pattern2, w_body):
                        new = re.findall(pattern1, q)
                        if re.findall(f'/media/django-summernote/{str(hoje)}/', q):
                            new_cid = os.path.join(settings.STATIC_URL+'monitoramento/'+str(hoje)+'/', (str(rr)
                                                    + new[0].split(f'cid:/media/django-summernote/{str(hoje)}/')[1]))
                        elif re.findall(f'/static/images/macros-monit/\w+[.]\w+.(?i:jpeg|jpg|gif|png|bmp)', q):
                            new_cid = os.path.join(settings.STATIC_URL + 'monitoramento/' + str(hoje) + '/',
                                                   (str(rr) +
                                                    new[0].split(f'cid:/static/images/macros-monit/')[1]))
                        elif re.findall(f'/static/images/macros-monit/\w+.(?i:jpeg|jpg|gif|png|bmp)', q):
                            new_cid = os.path.join(settings.STATIC_URL + 'monitoramento/' + str(hoje) + '/',
                                                   (str(rr) +
                                                    new[0].split(f'cid:/static/images/macros-monit/')[1]))
                        else:
                            try:
                                new_cid = os.path.join(settings.STATIC_URL + 'monitoramento/' + str(hoje) + '/',
                                                       (str(rr)
                                                        + new[0].split('cid:')[1]))
                            except Exception as e:
                                new_cid = os.path.join(settings.STATIC_URL + 'monitoramento/' + str(hoje) + '/',
                                                       (str(rr) + q))
                        w_body = w_body.replace(q, new_cid)
                elif re.findall(pattern1,w_body):
                    for q in re.findall(pattern1, w_body):
                        new = re.findall(pattern1, q)
                        try:
                            if re.findall(f'/media/django-summernote/{str(hoje)}/', q):
                                new_cid = os.path.join(settings.STATIC_URL + 'monitoramento/' + str(hoje) + '/',
                                                       (str(rr) +
                                                        new[0].split(f'cid:/media/django-summernote/{str(hoje)}/')[1]))
                            elif re.findall(f'/static/images/macros-monit/\w+[.]\w+.(?i:jpeg|jpg|gif|png|bmp)', q):
                                new_cid = os.path.join(settings.STATIC_URL + 'monitoramento/' + str(hoje) + '/',
                                                       (str(rr) +
                                                        new[0].split(f'cid:/static/images/macros-monit/')[1]))
                            elif re.findall(f'/static/images/macros-monit/\w+.(?i:jpeg|jpg|gif|png|bmp)', q):
                                new_cid = os.path.join(settings.STATIC_URL + 'monitoramento/' + str(hoje) + '/',
                                                       (str(rr) +
                                                        new[0].split(f'cid:/static/images/macros-monit/')[1]))
                            else:
                                try:
                                    new_cid = os.path.join(settings.STATIC_URL + 'monitoramento/' + str(hoje) + '/',
                                                           (str(rr)
                                                            + new[0].split('cid:')[1]))
                                except Exception as e:
                                    new_cid = os.path.join(settings.STATIC_URL + 'monitoramento/' + str(hoje) + '/',
                                                           (str(rr) + q))
                        except Exception as e:
                            print(f'ErrorType: {type(e).__name__}, Error: {e}')
                        else:
                            w_body = w_body.replace(q, new_cid)
                #continue
            except Exception as e:
                 print(f'insert data -- ErrorType: {type(e).__name__}, Error: {e}')
            else:
                #salva no banco de dados
                form = EmailMonitoramento.objects.filter(email_id=e_ref.strip())
                if form.exists() and form[0].tkt_ref.status != ('CONCLUIDO' or 'CANCELADO'):
                    try:
                        tkt = TicketMonitoramento.objects.get(pk=form[0].tkt_ref_id)
                    except Exception as e:
                        print(f'1ErrorType: {type(e).__name__}, Error: {e}')
                    else:
                        if form[0].ult_resp is not None:
                            aa = '<hr>' + e_from + ' -- ' + e_date + '\n' + e_body + '\n------Anterior-------\n' + form[0].ult_resp
                            bb = '<hr>' + e_from + ' -- ' + e_date + '<br>' + w_body + '<br>' + attatch + '<p>Anterior</p><hr>' + form[0].ult_resp_html
                        else:
                            aa = '<hr>' + e_from + ' -- ' + e_date + '\n' + e_body
                            bb = '<hr>' + e_from + ' -- ' + e_date + '<br>' + w_body + '<br>' + attatch
                        if tkt.status == 'ABERTO':
                            TicketMonitoramento.objects.filter(pk=form[0].tkt_ref_id).update(status='ANDAMENTO')
                        form.update(ult_resp=aa,ult_resp_html=bb, ult_resp_dt=e_date)
                        notify.send(sender=User.objects.get(pk=1), data=tkt.id, recipient=tkt.responsavel, verb='message',
                                    description=f"Você recebeu uma nova mensagem do ticket {tkt.id}")
                        pp.dele(i+1)
                elif form.exists() and form[0].tkt_ref.status == ('CONCLUIDO' or 'CANCELADO'):
                    pp.dele(i + 1)
                    pp.quit()
                    return redirect('portaria:monitticket')
                else:
                    try:
                        tkt = TicketMonitoramento.objects.get(msg_id=e_ref)
                    except Exception as e:
                        print(f'1ErrorType: {type(e).__name__}, Error: {e}')
                    else:
                        bb = '<hr>' + e_from + ' -- ' + e_date + w_body
                        EmailMonitoramento.objects.create(assunto=e_title, mensagem=bb, cc=e_cc, dt_envio=e_date,email_id=tkt.msg_id, tkt_ref_id=tkt.id)
                        notify.send(sender=User.objects.get(pk=1), data=tkt.id,recipient=tkt.responsavel, verb='message',
                                    description="Seu ticket foi criado.")
                    pp.dele(i + 1)
    pp.quit()
    return redirect('portaria:monitticket')

def replymail_monitoramento(request, tktid, area, myfile):
    media = ''
    pattern = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp)')
    orig = get_object_or_404(EmailMonitoramento, tkt_ref_id=tktid)
    keyga = {v: k for k, v in TicketMonitoramento.GARAGEM_CHOICES}
    getmailfil = EmailOcorenciasMonit.objects.filter(rsocial=orig.tkt_ref.get_filial_display(), ativo=1)
    mailfil = ''
    for i in getmailfil:
        mailfil += i.email + ', '
    send = [get_secret('ESEND_MN'), 'IGOR.ROSARIO@BORA.COM.BR','ROBERT.DIAS@BORA.COM.BR', request.user.email]+mailfil.split(',') + orig.cc.split(',') #
    if request.method == 'POST':
        msg1 = MIMEMultipart()
        msg = area
        if myfile is not None:
            for q in myfile:
                part = MIMEApplication(q.read(), name=str(q))
                part['Content-Disposition'] = 'attachment; filename="%s"' % q
                msg1.attach(part)
        if re.findall(pattern, msg):
            for q in re.findall(pattern, msg):
                media = q
                img_data = open(('/home/bora/www'+media),'rb').read()
                msgimg = MIMEImage(img_data, name=os.path.basename(media))
                msgimg.add_header('Content-ID', f'{media}')
                msg = msg.replace(('src="' + media + '"'), f'src="cid:{media}" ')
                msg1.attach(msgimg)
        sign = f'<br><img src="cid:{request.user}.jpg" width="600">'
        signimg = open(f'{settings.STATIC_ROOT}/images/macros-monit/{request.user}.jpg', 'rb').read()
        msgimg1 = MIMEImage(signimg, name=f'{request.user}.jpg', _subtype='jpg')
        msgimg1.add_header('Content-ID', f'{request.user}.jpg')
        msg1.attach(msgimg1)
        msg += sign
        msg1['Subject'] = orig.assunto
        msg1['In-Reply-To'] = orig.email_id
        msg1['References'] = orig.email_id
        msg_id = make_msgid(idstring=None, domain='bora.com.br')
        msg1['Message-ID'] = msg_id
        msg1['From'] = get_secret('EUSER_MN')#############
        msg1['To'] = orig.cc
        msg1['CC'] = orig.cc
        msg1.attach(MIMEText(msg, 'html', 'utf-8'))
        smtp_p = '587'##############
        user = 'bora@bora.tec.br'##############
        try:
            print('entrou no try')
            sm = smtplib.SMTP(get_secret('EHOST_MN'), smtp_p)################
            sm.set_debuglevel(1)
            sm.login(get_secret('EUSER_MN'), get_secret('EPASS_MN'))###############
            sm.sendmail(get_secret('EUSER_MN'), send, msg1.as_string())#############
            print('mandou o email')
        except Exception as e:
            print(f'ErrorType:{type(e).__name__}, Error:{e}')
    return redirect('portaria:monitticket')

def createtktandmail(request, **kwargs):
    pattern = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp)')
    msg1 = MIMEMultipart()
    getmailfil = EmailOcorenciasMonit.objects.filter(rsocial=kwargs['filial'], ativo=1)
    mailfil = ''
    for i in getmailfil:
        mailfil += i.email+','
    send = [get_secret('ESEND_MN'), 'IGOR.ROSARIO@BORA.COM.BR','ROBERT.DIAS@BORA.COM.BR', request.user.email]+mailfil.split(',') + kwargs['cc'].split(';') #
    if kwargs['file'] is not None:
        for q in kwargs['file']:
            part = MIMEApplication(q.read(), name=str(q))
            part['Content-Disposition'] = 'attachment; filename="%s"' % q
            msg1.attach(part)
    msgmail = kwargs['msg']
    keyga = {v: k for k, v in TicketMonitoramento.GARAGEM_CHOICES}
    if re.findall(pattern, kwargs['msg']):
        for q in re.findall(pattern, kwargs['msg']):
            media = q
            img_data = open(('/home/bora/www' + media), 'rb').read()
            msgimg = MIMEImage(img_data, name=os.path.basename(media))
            msgimg.add_header('Content-ID', f'{media}')
            msgmail = msgmail.replace(('<img src="' + media + '"'), f'<img src="cid:{media}" ')
            msg1.attach(msgimg)
    sign = f'<br><img src="cid:{request.user}.jpg" width="600">'
    signimg = open(f'{settings.STATIC_ROOT}/images/macros-monit/{request.user}.jpg', 'rb').read()
    msgimg1 = MIMEImage(signimg, name=f'{request.user}.jpg', _subtype='jpg')
    msgimg1.add_header('Content-ID', f'{request.user}.jpg')
    msg1.attach(msgimg1)
    msgmail += sign
    msg1.attach(MIMEText(msgmail, 'html', 'utf-8'))
    msg1['Subject'] = kwargs['assunto']
    msg1['From'] = get_secret('EUSER_MN')#################
    msg1['To'] = kwargs['cc']
    msg1['CC'] = kwargs['cc']
    msg_id = make_msgid(idstring=None, domain='bora.com.br')
    msg1['Message-ID'] = msg_id
    smtp_p = '587'################
    user = 'bora@bora.tec.br'##################
    try:
        sm = smtplib.SMTP(get_secret('EHOST_MN'), smtp_p)####################
        sm.set_debuglevel(1)
        sm.login(get_secret('EUSER_MN'), get_secret('EPASS_MN'))####################
    except Exception as e:
        messages.error(request, f'ErrorType:{type(e).__name__}, Error:{e}')
        print(f'ErrorType:{type(e).__name__}, Error:{e}')
    else:
        try:
            tkt = TicketMonitoramento.objects.create(nome_tkt=kwargs['assunto'], dt_abertura=timezone.now(),
                  responsavel=User.objects.get(username=kwargs['resp']), solicitante=request.user, remetente=kwargs['rem'],
                  destinatario=kwargs['dest'], cte=kwargs['cte'], status='ABERTO', categoria='Aguardando Recebimento',msg_id=msg_id,
                         filial=keyga[kwargs['filial']], tp_docto=kwargs['tp_docto'])
            sm.sendmail(get_secret('EUSER_MN'), send, msg1.as_string())  #############
        except Exception as e:
            messages.error(request, f'ErrorType:{type(e).__name__}, error:{e}')
        else:
            messages.success(request, f'Email enviado e ticket criado com sucesso. ID: {tkt.id}')

def closetkt(request, tktid):
    tkt = get_object_or_404(TicketMonitoramento, pk=tktid)
    if tkt and tkt.categoria != 'Aguardando Recebimento':
        TicketMonitoramento.objects.filter(pk=tkt.id).update(status='CONCLUIDO')
        messages.info(request, f'Ticket {tkt.id} alterado para CONCLUIDO com sucesso.')
    else:
        messages.error(request, 'Não autorizado encerramento do monitoramento.')
    return redirect('portaria:monitticket')

def createchamado(request, **kwargs):
    dict = kwargs
    pattern = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp)')
    msg1 = MIMEMultipart()
    msgmail = dict['area']
    if re.findall(pattern, dict['area']):
        for q in re.findall(pattern, dict['area']):
            media = q
            img_data = open(('/home/bora/www' + media), 'rb').read()
            msgimg = MIMEImage(img_data, name=os.path.basename(media))
            msgimg.add_header('Content-ID', f'{media}')
            msgmail = msgmail.replace(('<img src="' + media + '"'), f'<img src="cid:{media}" ')
            msg1.attach(msgimg)
    msg1.attach(MIMEText(msgmail, 'html', 'utf-8'))
    msg1['Subject'] = dict['assnt']
    msg1['From'] = get_secret('EUSER_CH') ################### alterar
    msg1['To'] = dict['solic'] ################### alterar
    msg_id = make_msgid(idstring=None, domain='bora.com.br')
    msg1['Message-ID'] = msg_id
    smtp_h = get_secret('ESMTP_CH')
    smtp_p = '587'
    try:
        sm = smtplib.SMTP(smtp_h, smtp_p, timeout=120)
        sm.set_debuglevel(1)
        sm.login(get_secret('EUSER_CH'), get_secret('EPASS_CH')) ################### alterar
    except Exception as e:
        messages.error(request, f'ErrorType:{type(e).__name__}, Error:{e}')
        print(f'ErrorType:{type(e).__name__}, Error:{e}')
    else:
        try:
            tkt = TicketChamado.objects.create(nome_tkt=dict['assnt'], dt_abertura=timezone.now(),
                                                     responsavel_id=dict['nresp'], servico=dict['nsvs'],
                                                     solicitante=dict['solic'], status=dict['nstts'],
                                                     msg_id=msg_id, departamento=dict['ndp'], filial=dict['nfil'])
        except Exception as e:
            print(e)
        sm.sendmail(get_secret('EUSER_CH'), [get_secret('EUSER_CH')] + dict['solic'].split(';'), msg1.as_string()) ################### alterar
        notify.send(request.user, recipient=tkt.responsavel, verb='message',
                    description="Seu ticket foi criado.")
        messages.success(request, 'Email enviado e ticket criado com sucesso')

def chamadoupdate(request,tktid,area):
    media = ''
    pattern = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp)')
    orig = get_object_or_404(EmailChamado, tkt_ref_id=tktid)
    if request.method == 'POST':
        msg1 = MIMEMultipart()
        msg = area
        if re.findall(pattern, msg):
            for q in re.findall(pattern,msg):
                media = q
                img_data = open(('/home/bora/www' + media), 'rb').read()
                msgimg = MIMEImage(img_data, name=os.path.basename(media))
                print(msgimg)
                msgimg.add_header('Content-ID', f'{media}')
                msg = msg.replace(('src="' + media + '"'), f'src="cid:{media}" ')
                msg1.attach(msgimg)
        msg1['Subject'] = orig.assunto
        msg1['In-Reply-To'] = orig.email_id
        msg1['References'] = orig.email_id
        msg_id = make_msgid(idstring=None, domain='bora.com.br')
        msg1['Message-ID'] = msg_id
        msg1['From'] = get_secret('EUSER_CH') ################### alterar
        msg1['To'] = orig.tkt_ref.solicitante
        msg1.attach(MIMEText(msg, 'html', 'utf-8'))
        smtp_h = get_secret('EHOST_CH')
        smtp_p = '587'
        user = get_secret('EUSER_CH')  ################### alterar
        passw = get_secret('EPASS_CH')
        try:
            sm = smtplib.SMTP(get_secret('ESMTP_CH'), smtp_p)
            sm.set_debuglevel(1)
            sm.login(get_secret('EUSER_CH'), get_secret('EPASS_CH')) ################### alterar################### alterar
            sm.sendmail(get_secret('EUSER_CH'), [get_secret('EUSER_CH')]+orig.tkt_ref.solicitante.split(';'), msg1.as_string())
        except Exception as e:
            print(f'ErrorType:{type(e).__name__}, Error:{e}')
    else:
        print('nao entrou no if')

def chamadoreadmail(request):
    #params
    tkt = None
    servico = ''
    hoje = datetime.date.today()
    attatch = ''
    host = get_secret('EHOST_CH')
    e_user = get_secret('EUSER_CH') ################### alterar
    e_pass = get_secret('EPASS_CH')
    pattern1 = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp)')
    pattern2 = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp).\w+.\w+')
    rr = random.random()

    #logando no email
    pp = poplib.POP3(host)
    pp.set_debuglevel(1)
    pp.user(e_user)
    pp.pass_(e_pass)

    num_messages = len(pp.list()[1]) #conta quantos emails existem na caixa
    for i in range(num_messages):
        try:
            raw_email = b'\n'.join(pp.retr(i+1)[1]) #pega email
            parsed_email = email.message_from_bytes(raw_email, policy=policy.compat32)
        except Exception as e:
            print(f'Error type:{type(e).__name__}, error: {e}')
        else:
            if parsed_email.is_multipart():
                #caminha pelas partes do email e armazena dados e arquivos
                for part in parsed_email.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get('Content-Type'))
                    if ctype == 'text/plain' and 'attatchment' not in cdispo:
                        body = part.get_payload(decode=True)
                    elif ctype == 'text/html' and 'attatchment' not in cdispo:
                        body = part.get_payload(decode=True)
                    if ctype == 'text/html' and 'attatchment' not in cdispo:
                        htbody = part.get_payload(decode=True)
                    filename = part.get_filename()
                    if filename:
                        path = settings.STATIC_ROOT + '/chamados/' + str(hoje) + '/'
                        locimg = os.path.join(path, filename)
                        if os.path.exists(os.path.join(path)):
                            fp = open(locimg, 'wb')
                            fp.write(part.get_payload(decode=True))
                            fp.close()
                            os.chmod(locimg, 0o777)
                            os.rename(locimg, os.path.join(path, (str(rr) + filename)))
                        else:
                            os.mkdir(path=path)
                            os.chmod(path, 0o777)
                            fp = open(locimg, 'wb')
                            fp.write(part.get_payload(decode=True))
                            fp.close()
                            os.chmod(locimg, 0o777)
                            os.rename(locimg, os.path.join(path, (str(rr) + filename)))
                        item = os.path.join((settings.STATIC_URL + 'chamados/' + str(hoje) + '/'), (str(rr) + filename))
                        aa = '<div class="mailattatch"><a href="'+item+'" download><img src="/static/images/downicon.png" width="40"><p>'+filename+'</p></a></div>'
                        attatch += aa
            else:
                body = parsed_email.get_payload(decode=True)
            #funcao para pegar codificacao
            cs = parsed_email.get_charsets()
            for q in cs:
                if q is None: continue
                else: cs = q
            '''
            inserir função para determinar qual tipo de serviço
            para cada email ti/dev/praxio etc
            ler a caixa de entrada e setar o servico
            '''
            #pega parametros do email
            e_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            e_title_unencoded = decode_header(parsed_email['Subject'])
            try:
                e_title = e_title_unencoded[0][0].decode(cs)
            except:
                e_title = parsed_email['Subject']

            e_from = parsed_email['From']
            if re.findall(r'<(.*?)>', e_from): e_from = re.findall(r'<(.*?)>', e_from)[0]
            e_to = parsed_email['To']
            if re.findall(r'<(.*?)>', e_to): e_to = re.findall(r'<(.*?)>', e_to)[0]
            e_cc = parsed_email['CC']
            if e_cc:
                if re.findall(r'<(.*?)>', e_cc): e_cc = re.findall(r'<(.*?)>', e_cc)[0]
            e_id = parsed_email['Message-ID']
            e_ref = parsed_email['References']
            if e_ref is None: e_ref = e_id
            else: e_ref = e_ref.split(' ')[0]

            #separa conteudo email, e pega attatchments
            e_body = body.decode(cs)
            if e_body:
                reply_parse = re.findall(r'(De:*\a*\w.*.\sEnviada em:+\s+\w.*.+[,]+\s+\d+\s+\w+\s+\w+\s+\w+\s+\d+\s+\d+:+\d.*)', e_body)
                if reply_parse:
                    e_body = e_body.split(reply_parse[0])[0].replace('\n', '<br>')
            w_body = '<div class="container chmdimg">' + htbody.decode(cs) + '</div>'
            if w_body:
                reply_html = re.findall(r'(<b><span+\s+\w.*.[>]+De:.*.Enviada em:.*.\s+\w.*.[,]+\s+\d+\s+\w+\s+\w+\s+\w+\s+\d+\s+\d+:+\d.*)',w_body)
                if reply_html:
                    w_body = w_body.split(reply_html[0])[0]
            if re.findall(pattern2, w_body):
                for q in re.findall(pattern2, w_body):
                    new = re.findall(pattern1, q)
                    if re.findall(f'/media/django-summernote/{str(hoje)}/', q):
                        new_cid = os.path.join(settings.STATIC_URL + 'chamados/' + str(hoje) + '/', (str(rr) +
                                                new[0].split(f'cid:/media/django-summernote/{str(hoje)}/')[1]))
                    else:
                        new_cid = os.path.join(settings.STATIC_URL + 'chamados/' + str(hoje) + '/',
                                               (str(rr) + new[0].split('cid:')[1]))
                    w_body = w_body.replace(q, new_cid)
            elif re.findall(pattern1, w_body):
                for q in re.findall(pattern1, w_body):
                    new = re.findall(pattern1, q)
                    try:
                        if re.findall(f'/media/django-summernote/{str(hoje)}/', q):
                            new_cid = os.path.join(settings.STATIC_URL + 'chamados/' + str(hoje) + '/', (str(rr) +
                                                   new[0].split(f'cid:/media/django-summernote/{str(hoje)}/')[1]))
                        else:
                            new_cid = os.path.join(settings.STATIC_URL + 'chamados/' + str(hoje)
                                                   + '/', (str(rr) + new[0].split('cid:')[1]))

                    except Exception as e:
                        print(f'ErrorType: {type(e).__name__}, Error: {e}')
                    else:
                        w_body = w_body.replace(q, new_cid)
            if e_to == 'chamado.praxio@bora.com.br':
                servico = 'PRAXIO'
            else:
                servico = 'DESENVOLVIMENTO'
            try:
                form = EmailChamado.objects.filter(email_id=e_ref)
                tkt = TicketChamado.objects.get(Q(msg_id=e_id) | Q(msg_id=e_ref))
            except Exception as e:
                print(e)
            try:
                if form.exists():
                    oldreply = form[0].ult_resp_html
                    if oldreply: newreply = w_body.split(oldreply[:50])
                    if form[0].ult_resp:
                        aa = '<hr>' + e_from + ' -- ' + e_date + '\n' + e_body + '\n------Anterior-------\n' + form[0].ult_resp
                        bb = '<hr>' + e_from + ' -- ' + e_date + '<br>' + newreply[0] + attatch + '<hr>' + form[0].ult_resp_html
                    else:
                        aa = '<hr>' + e_from + ' -- ' + e_date + '\n' + e_body
                        bb = '<hr>' + e_from + ' -- ' + e_date + '<br>' + w_body + attatch
                    form.update(ult_resp=aa, ult_resp_html=bb, ult_resp_dt=e_date)
                    notify.send(sender=User.objects.get(pk=1),
                                recipient=User.objects.filter(Q(groups__name='chamado')),
                                verb='message', description=f"Nova mensagem para o ticket {tkt.id}")
                elif form.exists() and form[0].tkt_ref.status == ('CANCELADO' or 'CONCLUIDO'):
                    messages.warning(request, 'Ticket já encerrado')
                    pp.dele(i + 1)
                    pp.quit()
                    return redirect('portaria:chamado')
                elif form.exists() == False and tkt != None:
                    mensagem = '<hr>' + e_from + ' -- ' + e_date + w_body + attatch
                    newmail = EmailChamado.objects.create(assunto=e_title, mensagem=mensagem, cc=e_cc, dt_envio=e_date,
                                                          email_id=e_id, tkt_ref=tkt)
                    notify.send(sender=User.objects.get(pk=1),
                                recipient=User.objects.filter(Q(groups__name='chamado')),
                                verb='message', description=f"Nova mensagem para o ticket {tkt.id}")
                else:
                    newtkt = TicketChamado.objects.create(solicitante=e_from, servico=servico, nome_tkt=e_title,
                                                          dt_abertura=e_date, status='ABERTO', msg_id=e_id)
                    mensagem = '<hr>' + e_from + ' -- ' + e_date + w_body + attatch
                    newmail = EmailChamado.objects.create(assunto=e_title, mensagem=mensagem, cc=e_cc, dt_envio=e_date,
                                                          email_id=e_id, tkt_ref=newtkt)
                    notify.send(sender=User.objects.get(pk=1),
                                recipient=User.objects.filter(Q(groups__name='chamado')),
                                verb='message', description=f"Novo Chamado aberto: id {newtkt.id}")
            except Exception as e:
                print(e)
            else:
                pp.dele(i + 1)
            pp.quit()
    return redirect('portaria:chamado')

def isnotifyread(request, notifyid):
    nid = get_object_or_404(Notification, pk=notifyid)
    next = request.GET.get('next')
    try:
        Notification.objects.filter(pk=nid.id).update(unread=False)
    except Exception as e:
        print(f'ErrorType:{type(e).__name__}, Error:{e}')
    return redirect(next)

def setallread(request, user):
    next = request.GET.get('next')
    if user:
        cases = Notification.objects.filter(recipient=user)
        for n in cases:
            Notification.objects.filter(pk=n.id).update(unread=False)
    return redirect(next)

def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def testeconn(request):
    conndb()