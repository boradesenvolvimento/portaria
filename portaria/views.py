#imports geral
import asyncio
import io
import json
import random
import csv
import datetime
import email, smtplib
import os
import re
import socket
import tempfile
import textwrap
import poplib
from collections import Counter
from email.mime.base import MIMEBase
from io import BytesIO
from zipfile import ZipFile

import numpy as np
import pandas as pd
from email import policy, encoders
from email.header import decode_header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import make_msgid

import requests
from asgiref.sync import sync_to_async
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.crypto import get_random_string
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
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest, Http404, FileResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.defaultfilters import upper
from django.urls import reverse
from django.utils import timezone, dateformat
from django.views import generic
from xml.dom import minidom

from xlsxwriter import Workbook

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
                km = form.cleaned_data['kilometragem']
                days_back = timezone.now() - datetime.timedelta(days=30)
                loc_placa = Cadastro.objects.filter(placa=s_query, hr_chegada__gte=days_back,
                                                    hr_saida=None).order_by('-hr_chegada').first()
                try:
                    Cadastro.objects.get(pk=loc_placa.id)
                except AttributeError:
                    messages.error(request, 'Não encontrado')
                    return render(request, 'portaria/portaria/cadastrosaida.html', {'form':form})
                else:
                    Cadastro.objects.filter(pk=loc_placa.id).update(hr_saida=timezone.now(), destino=q_query,
                                                                    kilometragem=km, autor=request.user)
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
    tp_fil = GARAGEM_CHOICES
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
    tp_emp = Cliente.objects.all().order_by('razao_social')
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
    form = Cliente.objects.filter(~Q(saldo=0), intex='CLIENTE').order_by('razao_social')
    tcount = form.aggregate(total=Sum('saldo'))
    return render(request, 'portaria/palete/paletecliente.html', {'form':form,'tcount':tcount})

def saidapalete(request):
    tp_fil = TIPO_GARAGEM
    tp_emp = Cliente.objects.all().order_by('razao_social')
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
    form = ChecklistFrota.objects.all().order_by('-idchecklist')
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
            aux_moradia=Coalesce(Sum('nfservicopj__aux_moradia',filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
            desc_convenio=Coalesce(Sum('nfservicopj__desc_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
            outros_desc=Coalesce(Sum('nfservicopj__outros_desc', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
            ) \
            .annotate(total=((F('salario') + F('ajuda_custo') + F('faculdade') + F('cred_convenio') + F('outros_cred') + F('aux_moradia')) - (F('adiantamento') + F('desc_convenio') + F('outros_desc'))))
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
    grps = TipoServicosManut.objects.values_list('grupo_servico', flat=True).distinct()
    if request.method == 'POST':
        grp = request.POST.get('grp')
        tp_sv = request.POST.get('tp_sv')
        if grp and tp_sv:
            try:
                TipoServicosManut.objects.create(grupo_servico=grp, tipo_servico=tp_sv)
            except Exception as e:
                print(e)
            messages.success(request, 'Cadastrado com sucesso')
            return redirect('portaria:frotacadastros')
    return render(request, 'portaria/frota/cadtpservico.html', {'grps':grps})

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
    svsss = ServJoinManu.objects.filter(id_os_id=get_os.id)
    if get_os.dt_saida == None:
        if request.method == 'POST':
            idsvs = request.POST.getlist('idsvs')
            dtsaida = request.POST.get('dtsaida')
            vlmao = request.POST.getlist('vlmao')
            vlpeca = request.POST.getlist('vlpeca')
            prod = request.POST.getlist('produto')
            forn = request.POST.getlist('fornecedor')
            localmanu = request.POST.getlist('localmanu')
            feito = request.POST.getlist('feitochk')
            if dtsaida and vlmao and vlpeca:
                try:
                    array = []
                    date_dtsaida = datetime.datetime.strptime(dtsaida, '%Y-%m-%d').date()
                    for i in range(0, len(idsvs)):
                        array.append({'idsvs':idsvs[i], 'vlmao':vlmao[i].replace(',','.'),
                                      'vlpeca':vlpeca[i].replace(',','.'), 'prod':prod[i], 'forn':forn[i],
                                      'localmanu':localmanu[i], 'feito':int(feito[i])})
                except ValueError as e:
                    messages.error(request, 'Por favor digite uma data válida')
                    return render(request, 'portaria/frota/manusaida.html',{'get_os':get_os})
                else:
                    between_days = (date_dtsaida - get_os.dt_entrada).days
                    ManutencaoFrota.objects.filter(pk=get_os.id).update(dt_saida=date_dtsaida,
                                                                        dias_veic_parado=str(between_days),
                                                                        status='PENDENTE',
                                                                        autor=request.user)
                    for q in array:
                        try:
                            ServJoinManu.objects.filter(pk=q['idsvs']).update(valor_maodeobra=q['vlmao'],
                                                                              valor_peca=q['vlpeca'],produto=q['prod'],
                                                                              fornecedor=q['forn'],
                                                                              feito=q['feito'],
                                                                              local_manu=q['localmanu'])
                        except Exception as e:
                            print(e)
                    messages.success(request, f'Saída cadastrada para OS {get_os.id}, placa {get_os.veiculo}')
                    return redirect('portaria:manutencaoview')
        return render(request, 'portaria/frota/manusaida.html',{'get_os':get_os,'svsss':svsss})
    else:
        messages.error(request, 'Saída já cadastrada para OS')
        return redirect('portaria:manutencaofrota')

def agendamentomanu(request):
    array = []
    autor = request.user
    gp_servs = TipoServicosManut.objects.values_list('grupo_servico', flat=True).distinct()
    for q in gp_servs:
        tp_servs = TipoServicosManut.objects.filter(grupo_servico=str(q))
        concat = [str(q), tp_servs]
        array.append(concat)
    if request.method == 'POST':
        placav = request.POST.get('placav')
        tp_sv = request.POST.getlist('tp_servico')
        try:
            placa = get_object_or_404(Veiculos, prefixoveic=placav)
        except Exception:
            messages.error(request, 'Placa não encontrada')
            return redirect('portaria:agendamentomanu')
        else:
            if placa and tp_sv:
                try:
                    os = ManutencaoFrota.objects.create(veiculo_id=placa.codigoveic,autor=autor, motorista=autor,
                                                        tp_manutencao='PRE')
                    for q in tp_sv:
                        ServJoinManu.objects.create(id_svs_id=q, autor=autor, id_os_id=os.id)
                except Exception as e:
                    print(e)
                else:
                    return redirect('portaria:manutencaoprint', osid=os.id)
    return render(request, 'portaria/frota/agendamentomanu.html', {'array':array})

def updatemanu(request, osid):
    os = get_object_or_404(ManutencaoFrota, pk=osid)
    form = ManutencaoForm
    autor = request.user
    motorista = os.motorista
    ult_manu = Veiculos.objects.filter(pk=os.veiculo.codigoveic).values_list('manutencaofrota__dt_saida', flat=True) \
        .order_by('-manutencaofrota__dt_saida').first()
    if ult_manu == None: ult_manu = timezone.now()
    if request.method == 'POST':
        form = ManutencaoForm(request.POST or None, instance=os)
        if form.is_valid():
            try:
                manu = form.save(commit=False)
                manu.veiculo_id = os.veiculo.codigoveic
                manu.motorista = motorista
                manu.dt_ult_manutencao = ult_manu
                manu.dt_entrada = timezone.now()
                manu.status = 'ANDAMENTO'
                manu.autor = autor
                manu.save()
            except Exception as e:
                print(e)
            else:
                messages.success(request, 'Atualizado com sucesso.')
                return redirect('portaria:manutencaoview')
    return render(request, 'portaria/frota/updatemanu.html', {'os':os, 'form':form})

def addservico(request, osid):
    os = get_object_or_404(ManutencaoFrota, pk=osid)
    array = []
    autor = request.user
    gp_servs = TipoServicosManut.objects.values_list('grupo_servico', flat=True).distinct()
    for q in gp_servs:
        tp_servs = TipoServicosManut.objects.filter(grupo_servico=str(q))
        concat = [str(q), tp_servs]
        array.append(concat)
    if request.method == 'POST':
        tp_sv = request.POST.getlist('tp_servico')
        if tp_sv:
            try:
                for q in tp_sv:
                    ServJoinManu.objects.create(id_svs_id=q, autor=autor, id_os_id=os.id)
            except Exception as e:
                print(e)
            else:
                messages.success(request, 'Serviços cadastrados com sucesso.')
                return redirect('portaria:manutencaoview')
    return render(request, 'portaria/frota/addservico.html', {'array':array, 'os':os})

class ManutencaoListView(generic.ListView):
    template_name = 'portaria/frota/manutencaoview.html'
    context_object_name = 'lista'

    def get_queryset(self):
        qs = ManutencaoFrota.objects.filter(dt_saida=None,).order_by('tp_manutencao','dt_entrada')
        try:
            placa = self.request.GET.get('isplaca')
            if placa:
                qs = ManutencaoFrota.objects.filter(Q(veiculo__prefixoveic=placa) | Q(id=placa)).exclude(dt_saida__isnull=False).order_by('dt_entrada')
        except ObjectDoesNotExist:
            raise Exception('Valor digitado inválido')
        return qs

    def get_context_data(self, **kwargs):
        data = ServJoinManu.objects.all()
        metrics = ManutencaoFrota.objects.all().annotate(
        preventiva=Count('id', filter=Q(tp_manutencao='PREVENTIVA')),
        corretiva=Count('id', filter=Q(tp_manutencao='CORRETIVA')),
        concluido=Count('id', filter=Q(status='CONCLUIDO',dt_entrada__month=datetime.datetime.now().month,
                                       dt_entrada__year=datetime.datetime.now().year)))\
            .aggregate(prev=Sum('preventiva'),corr=Sum('corretiva'),conc=Sum('concluido'))
        context = super().get_context_data(**kwargs)
        context['form'] = data
        context['metrics'] = metrics
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
                cur.close()
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
            a = EmailOcorenciasMonit.objects.filter(email=q, ativo=1)
            obj = EmailOcorenciasMonit.objects.filter(pk=a[0].id).update(ativo=0)
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
    metrics = TicketMonitoramento.objects.annotate(
        total=Count('id', filter=~Q(status__in=['CONCLUIDO','CANCELADO'],
        dt_abertura__month=datetime.datetime.now().month,dt_abertura__year=datetime.datetime.now().year)),
        hoje=Count('id', filter=Q(dt_abertura=hj)), andamento=Count('id', filter=Q(status='ANDAMENTO',
        dt_abertura__month=datetime.datetime.now().month,dt_abertura__year=datetime.datetime.now().year)),
        aberto=Count('id', filter=Q(status='ABERTO', dt_abertura__month=datetime.datetime.now().month,
        dt_abertura__year=datetime.datetime.now().year)), totalfull=Count('id',
        filter=Q(dt_abertura__month=datetime.datetime.now().month,dt_abertura__year=datetime.datetime.now().year))
    ).aggregate(total1=Sum(F('andamento')+F('aberto')), hoje1=Sum('hoje'), andamento1=Sum('andamento'), aberto1=Sum('aberto'),
                totalf=Sum('totalfull'))

    totfunc = User.objects.filter(groups__name='monitoramento')\
        .annotate(total=Count('responsavel__id',filter=Q(responsavel__status__in=['ABERTO', 'ANDAMENTO'])),
        diario=Count('responsavel__id',filter=Q(responsavel__dt_abertura=datetime.date.today())),
        concluido=Count('responsavel__id',filter=Q(responsavel__dt_abertura__month=datetime.datetime.now().month,
        responsavel__dt_abertura__year=datetime.datetime.now().year, responsavel__status='CONCLUIDO'))
        ).exclude(total=0).order_by('username')
    totfuncself = User.objects.filter(groups__name='monitoramento', responsavel__responsavel=request.user)\
        .annotate(total=Count('responsavel__id',filter=Q(responsavel__status__in=['ABERTO', 'ANDAMENTO'])),
        diario=Count('responsavel__id',filter=Q(responsavel__dt_abertura=datetime.date.today())),
        concluido=Count('responsavel__id',filter=Q(responsavel__dt_abertura__month=datetime.datetime.now().month,
        responsavel__dt_abertura__year=datetime.datetime.now().year, responsavel__status='CONCLUIDO')),
        ).order_by('username')
    return render(request, 'portaria/monitoramento/ticketmetrics.html', {'metrics':metrics,'totfunc':totfunc,
                                                                         'totfuncself':totfuncself})

def includemailtkt(request):
    ac = EmailOcorenciasMonit.objects.values_list('rsocial', flat=True).distinct()
    if request.method == 'POST':
        empresa = request.POST.get('empresas')
        mail = request.POST.get('getmail')
        count = request.POST.get('setcount')
        if empresa and mail:
            EmailOcorenciasMonit.objects.create(email=mail, rsocial=empresa, ativo=1)
            if count:
                ncount = int(count)
                for c in range(0, ncount):
                    d = c + 1
                    mails = request.POST.get(f'getmail{d}')
                    if mails:
                        try:
                            EmailOcorenciasMonit.objects.create(email=mails, rsocial=empresa, ativo=1)
                        except Exception as e:
                            messages.error(request, f'Erro ao cadastrar os emails, ErrorType:{type(e).__name__}, Error: {e}')
                        finally:
                            redirect('portaria:monitticket')
                    else:
                        continue
    return render(request, 'portaria/monitoramento/includemailtkt.html', {'ac':ac})
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

def etiquetas(request):
    gachoices = TicketMonitoramento.GARAGEM_CHOICES
    docchoices = TIPO_DOCTO_CHOICES
    if request.method == 'POST':
        lista = request.POST.getlist('getcte')
        ga = int(request.POST.get('getga'))
        doc = int(request.POST.get('getdoc'))
        nota = int(request.POST.get('getnota'))
        if len(lista) == 1:
            lista = lista[0]
        else:
            lista = tuple(lista)
        try:
            conn = settings.CONNECTION
            cur = conn.cursor()
            cur.execute(f"""
                        SELECT F4.NOTA_FISCAL, F4.VOLUMES, F1.CONHECIMENTO
                        FROM
                            FTA001 F1,
                            FTA004 F4
                        WHERE
                            F1.EMPRESA = F4.EMPRESA			AND
                            F1.FILIAL = F4.FILIAL			AND
                            F1.GARAGEM = F4.GARAGEM			AND
                            F1.CONHECIMENTO = F4.CONHECIMENTO	AND
                            F1.SERIE = F4.SERIE			AND
                            F1.TIPO_DOCTO = F4.TIPO_DOCTO		AND
                        
                            F1.CONHECIMENTO IN {lista}			AND
                            F1.ID_GARAGEM = {ga}			AND
                            F1.TIPO_DOCTO = {doc}       AND
                            F4.NOTA_FISCAL = {nota}     AND
                            F1.DATA_EMISSAO BETWEEN ((SYSDATE)-90) 	AND (SYSDATE)
                        """)
            res = dictfetchall(cur)
            cur.close()
        except Exception as e:
            raise e
        else:
            for i in res:
                try:
                    check = EtiquetasDocumento.objects.filter(garagem=ga, tp_doc=doc, nr_doc=i['CONHECIMENTO'],
                                                         nota=i['NOTA_FISCAL'], volume=i['VOLUMES'])
                    if not check:
                        EtiquetasDocumento.objects.create(garagem=ga, tp_doc=doc, nr_doc=i['CONHECIMENTO'],
                                                         nota=i['NOTA_FISCAL'], volume=i['VOLUMES'])
                except Exception as e:
                    print(f'Error: {e}, error_type:{type(e).__name__}')
            request.session['dict'] = res
            return redirect('portaria:createetiquetas')
    return render(request, 'portaria/etiquetas/etiquetas.html', {'gachoices':gachoices, 'docchoices':docchoices})

def createetiquetas(request):
    lista = request.session['dict']
    array = []
    for j in lista:
        for i in range(0, j['VOLUMES']):
            if i % 2 == 0:
                a = (str(i+1)+j['NOTA_FISCAL'])
                b = (str(i+2)+j['NOTA_FISCAL'])
                array.append(f'''
                    CT~~CD,~CC^~CT~
                    ^XA
                    ~TA000
                    ~JSN
                    ^LT0
                    ^MNW
                    ^MTD
                    ^PON
                    ^PMN
                    ^LH0,0
                    ^JMA
                    ^PR4,4
                    ~SD15
                    ^JUS
                    ^LRN
                    ^CI27
                    ^PA0,1,1,0
                    ^XZ
                    ^XA
                    ^MMT
                    ^PW799
                    ^LL240
                    ^LS0
                    ^FO4,111^GB385,0,2^FS
                    ^FO73,15^GB250,87,2^FS
                    ^FO74,56^GB248,0,2^FS
                    ^FT165,46^A0N,23,23^FH\^CI28^FDNota: {j['NOTA_FISCAL']}^FS^CI27
                    ^FT131,87^A0N,23,23^FH\^CI28^FDVolume: {i+1} de {(j['VOLUMES'])}^FS^CI27
                    ^BY2,3,82^FT73,211^BCN,,N,N
                    ^FH\^FD>:{ a }^FS
                    ^FO404,111^GB385,0,2^FS
                    ^FO473,15^GB250,87,2^FS
                    ^FO474,56^GB248,0,2^FS
                    ^FT565,46^A0N,23,23^FH\^CI28^FDNota: {j['NOTA_FISCAL']}^FS^CI27
                    ^FT531,87^A0N,23,23^FH\^CI28^FDVolume: {i+2} de {(j['VOLUMES'])}^FS^CI27
                    ^BY2,3,82^FT473,211^BCN,,N,N
                    ^FH\^FD>:{ b }^FS
                    ^PQ1,0,1,Y
                    ^XZ
                    '''.encode('utf-8'))
    if lista:
        if request.POST.get('getbtnprint') and request.POST.get('getbtnprint') == 'Click':
            printetiquetas(array)
            messages.success(request, 'Impressões iniciadas')
            return redirect('portaria:etiquetas')
        return render(request, 'portaria/etiquetas/generate_pdf.html', {'lista':lista})
    else:
        messages.error(request, 'Não encontrado para este romaneio')
        return redirect('portaria:etiquetas')

def contagemetiquetas(request):
    gachoices = GARAGEM_CHOICES
    docchoices = EtiquetasDocumento.TIPO_DOCTO_CHOICES
    if request.method == 'POST':
        cte = request.POST.get('getcte')
        ga = request.POST.get('getga')
        tp_doc = request.POST.get('tp_doc')
        nf = request.POST.get('getnf')
        if cte and ga and nf:
            if len(nf) < 10:
                nf = ('0'*(10-len(nf))) + nf
            else: pass
            request.session['dict'] = {'cte':cte, 'nf':nf, 'ga':ga, 'tp_doc':tp_doc}
            return redirect('portaria:bipagemetiquetas')
    return render(request,'portaria/etiquetas/contagemetiquetas.html', {'gachoices':gachoices, 'docchoices':docchoices})

def bipagemetiquetas(request):
    dict = request.session['dict']
    docs = EtiquetasDocumento.objects.filter(nr_doc=dict['cte'], nota=dict['nf'],
                                             garagem=dict['ga'], tp_doc=dict['tp_doc'])
    cont = 0
    for k in docs:
        cont += k.volume
    try:
        qnt = BipagemEtiqueta.objects.filter(doc_ref=docs[0]).count()
    except IndexError:
        messages.error(request, 'Não encontrado, verifique os valores inseridos')
        return redirect('portaria:contagemetiquetas')
    else:
        if qnt < cont:
            if request.method == 'POST':
                test = request.POST.getlist('getbarcode')
                try:
                    test = ' '.join(test).split()
                except:
                    pass
                if len(test) == cont:
                    for i in test:
                        if not BipagemEtiqueta.objects.filter(cod_barras=i):
                            check = docs.filter(nota=i[-10:])
                            if check:
                                BipagemEtiqueta.objects.create(cod_barras=i,nota=i[-10:],doc_ref=docs[0],autor=request.user)
                            else:
                                messages.error(request, f'{i} não pertence ao romaneio, gentileza verificar.')
                                return HttpResponse('<script>window.history.back()</script>')
                        else:
                            check = docs.filter(nota=i[-10:])
                            if check:
                                BipagemEtiqueta.objects.filter(cod_barras=i).update(pub_date=timezone.now())
                    messages.success(request, 'Bipagem cadastrada com sucesso')
                    return redirect('portaria:contagemetiquetas')
                else:
                    messages.error(request, 'Quantidade de notas enviadas inválida, gentileza verificar.')
                    return HttpResponse('<script>window.history.back()</script>')
        else:
            messages.error(request, 'Contagem já atingiu a quantidade de volumes')
            return redirect('portaria:contagemetiquetas')
    return render(request, 'portaria/etiquetas/bipagemetiquetas.html', {'docs':docs, 'nrdoc':dict['cte'],
                                                                        'cont':cont})

def retornoetiqueta(request):
    gachoices = GARAGEM_CHOICES
    if request.method == 'POST':
        nflist = request.POST.getlist('getnf')
        for q in nflist:
            if EtiquetasDocumento.objects.filter(nota=q[-10:]) and \
                    RetornoEtiqueta.objects.filter(nota_fiscal=q,
                    saida__month=datetime.datetime.now().month,saida__year=datetime.datetime.now().year
                                                   ).exists() == False:
                RetornoEtiqueta.objects.create(nota_fiscal=q)
            else:
                pass
        messages.warning(request, 'Cadastros finalizados.')
        return redirect('portaria:retornoetiqueta')
    return render(request, 'portaria/etiquetas/retornoetiqueta.html', {'gachoices':gachoices})

def etiquetas_palete(request):
    gachoices = TicketMonitoramento.GARAGEM_CHOICES
    ac = Cliente.objects.all()
    last = EtiquetasPalete.objects.all().order_by('-id').values_list('cod_barras', flat=True).first()
    new = str(int(last) + 1).zfill(10)
    array = []
    if request.method == 'POST':
        ga = request.POST.get('getga')
        vol = request.POST.get('getvol')
        cli = request.POST.get('getcli')
        man = request.POST.get('getmanifesto')
        nf = request.POST.get('getnf')
        loc = request.POST.get('getloc')
        isprint = request.POST.get('isprint')
        if ga and vol and cli:
            etq = EtiquetasPalete.objects.create(cod_barras=new, filial=ga, volumes=vol, cliente=cli,
                                                 nota_fiscal=nf, localizacao=loc, autor=request.user)
            if man:
                etq.manifesto = man
                etq.save()
            if isprint == 'on':
                array.append(f'''
                                CT~~CD,~CC^~CT~
                                ^XA
                                ~TA000
                                ~JSN
                                ^LT0
                                ^MNW
                                ^MTD
                                ^PON
                                ^PMN
                                ^LH0,0
                                ^JMA
                                ^PR4,4
                                ~SD15
                                ^JUS
                                ^LRN
                                ^CI27
                                ^PA0,1,1,0
                                ^XZ
                                ^XA
                                ^MMT
                                ^PW799
                                ^LL240
                                ^LS0
                                ^FO4,111^GB385,0,2^FS
                                ^FO73,15^GB250,87,2^FS
                                ^FO74,56^GB248,0,2^FS
                                ^FT165,46^A0N,23,23^FH\^CI28^FDPalete^FS^CI27
                                ^FT131,87^A0N,23,23^FH\^CI28^FDVolume: {etq.volumes}^FS^CI27
                                ^BY2,3,82^FT73,211^BCN,,N,N
                                ^FH\^FD>:{etq.cod_barras}^FS
                                ^FO404,111^GB385,0,2^FS
                                ^FO473,15^GB250,87,2^FS
                                ^FO474,56^GB248,0,2^FS
                                ^FT565,46^A0N,23,23^FH\^CI28^FDPalete^FS^CI27
                                ^FT531,87^A0N,23,23^FH\^CI28^FDVolume: {etq.volumes}^FS^CI27
                                ^BY2,3,82^FT473,211^BCN,,N,N
                                ^FH\^FD>:{etq.cod_barras}^FS
                                ^PQ1,0,1,Y
                                ^XZ
                            '''.encode('utf-8'))
                printetiquetas(array)
            messages.success(request, 'Etiqueta Palete gerado com sucesso.')
            return redirect('portaria:etiquetas_palete')
    return render(request, 'portaria/etiquetas/etiquetas_palete.html',{
        'gachoices':gachoices,'ac':ac})

def bipagem_palete(request):
    gachoices = TicketMonitoramento.GARAGEM_CHOICES
    if request.method == 'POST':
        code = request.POST.get('idbarcode')
        vol = request.POST.get('volume')
        man = request.POST.get('manifesto')
        ga = request.POST.get('getga')
        if code:
            try:
                getobj = get_object_or_404(EtiquetasPalete, cod_barras=code)
            except Exception as e:
                print(f'Error:{e}, error_type:{type(e).__name__}')
                messages.error(request, 'Não encontrado etiqueta com essa numeração')
            else:
                bip = BipagemPalete.objects.create(filial=ga, cod_barras=code, volume_conf=vol, autor=request.user,
                                                    etq_ref=getobj)
                if man:
                    bip.manifesto = man
                    bip.save()
                print(f'salvo no banco de dados bipagem nº{bip.id}')
                messages.success(request, 'Bipado com sucesso.')
    return render(request, 'portaria/etiquetas/bipagem_palete.html', {'gachoices':gachoices})

def etqrelatorio(request):
    gachoices = TicketMonitoramento.GARAGEM_CHOICES
    return render(request, 'portaria/etiquetas/etiquetasrelatorio.html', {'gachoices':gachoices})

def romaneioxml(request):
    return render(request, 'portaria/etc/romaneioindex.html')

def painelromaneio(request):
    context = RomXML.objects.all().filter(pub_date__month=datetime.datetime.now().month,
                                          pub_date__year=datetime.datetime.now().year).order_by('-pub_date')
    getrem = RomXML.objects.all().values_list('remetente', flat=True).distinct()
    if request.method == 'GET':
        dt1 = request.GET.get('data1')
        dt2 = request.GET.get('data2')
        rem = request.GET.get('remetente')
        if dt1 and dt2:
            dt1p = datetime.datetime.strptime(dt1, '%Y-%m-%d').replace(hour=00, minute=00)
            dt2p = datetime.datetime.strptime(dt2, '%Y-%m-%d').replace(hour=23, minute=59)
            if rem:
                context = RomXML.objects.filter(pub_date__gte=dt1p,pub_date__lte=dt2p,
                                                remetente=rem).order_by('-pub_date')
            else:
                context = RomXML.objects.filter(pub_date__gte=dt1p, pub_date__lte=dt2p).order_by('-pub_date')

    if request.method == 'POST':
        romidd = request.POST.getlist('romid')
        tp_dld = request.POST.get('tp_dld')
        if romidd:
            if tp_dld == 'Completo':
                romaneio = SkuRefXML.objects.filter(xmlref__id__in=romidd).annotate(
                    nf1=F('xmlref__nota_fiscal'),
                    municipio1=F('xmlref__municipio'), uf1=F('xmlref__uf'), codigo1=F('codigo'),
                    qnt_un1=F('qnt_un'), desc_prod1=F('desc_prod'), rem=F('xmlref__remetente'),
                    romaneio_id=F('xmlref_id'), volume=F('xmlref__volume'))
            elif tp_dld == 'Simples':
                romaneio = RomXML.objects.filter(id__in=romidd).annotate(
                    nf1=F('nota_fiscal'),volume1=F('volume'),uf1=F('uf'), rem=F('remetente')
                )
            elif tp_dld == 'Remetente':
                romaneio = SkuRefXML.objects.filter(xmlref__id__in=romidd).annotate(
                    municipio1=F('xmlref__municipio'), uf1=F('xmlref__uf'), codigo1=F('codigo'),
                    qnt_un1=F('qnt_un'), desc_prod1=F('desc_prod'), rem=F('xmlref__remetente'),
                    romaneio_id=F('xmlref__nota_fiscal'), volume=F('xmlref__volume'), valor=F('xmlref__vlr_nf'),
                    tp_un1=F('tp_un'), peso=F('xmlref__peso')
                )
            elif tp_dld == 'Destinatario':
                romaneio = SkuRefXML.objects.filter(xmlref__id__in=romidd).annotate(
                    municipio1=F('xmlref__municipio'), uf1=F('xmlref__uf'), codigo1=F('codigo'),qnt_un1=F('qnt_un'),
                    desc_prod1=F('desc_prod'), dest=F('xmlref__destinatario'), romaneio_id=F('xmlref__nota_fiscal'),
                    volume=F('xmlref__volume'), valor=F('xmlref__vlr_nf'), tp_un1=F('tp_un'), peso=F('xmlref__peso'),
                )
            elif tp_dld == 'XMLS':
                try:
                    rar = getFiles(*romidd)
                except Exception as e:
                    raise e
                if rar:
                    return rar
            else:
                messages.error(request, f'Selecione o tipo de download.')
                return redirect('portaria:painelromaneio')
            try:
                if romaneio:
                    sheet = romxmltoexcel(*romaneio, tp_dld=tp_dld)
                else:
                    pass
            except KeyError:
                messages.error(request, f'Não encontrado valores para sua solicitação.')
                return redirect('portaria:painelromaneio')
            except Exception as e:
                print(e, type(e).__name__)
                messages.error(request, f'Algo deu errado, verifique e tente novamente.')
                return redirect('portaria:painelromaneio')
            else:
                if sheet:
                    return sheet
    return render(request, 'portaria/etc/painelromaneio.html', {'context':context, 'getrem':getrem})

def entradaromaneio(request):
    if request.method == 'POST':
        emissao = datetime.datetime.strptime(request.POST.get('emissao'), '%Y-%m-%dT%H:%M')
        nrnota = request.POST.get('nrnota')
        remet = upper(request.POST.get('remet'))
        destin = upper(request.POST.get('destin'))
        peso = request.POST.get('peso')
        volume = request.POST.get('volume')
        vlr_nf = request.POST.get('vlr_nf')
        uf = upper(request.POST.get('uf'))
        municipio = upper(request.POST.get('municipio'))
        autor = request.user

        codigo = request.POST.get('codigo')
        descr = request.POST.get('descr')
        tp_un = request.POST.get('tp_un')
        qnt_un = request.POST.get('qnt_un')
        count = request.POST.get('setcount')
        if emissao and nrnota and remet and destin and volume and vlr_nf:
            try:
                rom = RomXML.objects.create(dt_emissao=emissao, nota_fiscal=nrnota, remetente=remet, destinatario=destin,
                                            peso=peso,volume=volume,vlr_nf=vlr_nf,autor=autor,municipio=municipio, uf=uf)
            except Exception as e:
                print(f'Error:{e}, error-type:{type(e).__name__}')
            else:
                SkuRefXML.objects.create(codigo=codigo,desc_prod=descr, tp_un=tp_un,qnt_un=qnt_un, xmlref=rom)
                if count:
                    ncount = int(count)
                    if ncount > 0:
                        for c in range(0, ncount):
                            d = c + 1
                            codigo = upper(request.POST.get(f'codigo{str(d)}'))
                            descr = upper(request.POST.get(f'descr{str(d)}'))
                            tp_un = upper(request.POST.get(f'tp_un{str(d)}'))
                            qnt_un = upper(request.POST.get(f'qnt_un{str(d)}'))
                            if codigo and descr and tp_un and qnt_un:
                                SkuRefXML.objects.create(codigo=codigo,desc_prod=descr, tp_un=tp_un,qnt_un=qnt_un,
                                                     xmlref=rom)
    return render(request, 'portaria/etc/romaneiomanual.html')

@sync_to_async
def entradaxml(request, args=None):
    cnpjs = ["05504835000100","05504835000283","05504835000526","05504835000364","05504835000607","05504835000445",
             "05504835000798","05504835000879","05504835000950","05504835001093","14059252000109","14059252000281",
             "14059252000443","14059252000362","14059252000524","44536137000130","44536137000211","44536137000300",
             "44536137000483","44536137000564","44536137000645","44536137000726","44536137000807","44329445000195",
             "44326860000195","44307910000197","44307936000135","36995897000188"]

    if request.method == 'POST':
        files = request.FILES.getlist('getxml')
    else:
        print('recebeu o arquivo')
        files = args
    for file in files:
        try:
            mydoc = minidom.parse(file)
        except AttributeError:
            s = io.BytesIO()
            s.write(file)
            s.seek(0)

            xml = s
            mydoc = minidom.parseString(xml.getvalue())
            file = InMemoryUploadedFile(
                xml,
                field_name='xml',
                name=f'{datetime.date.today()}.xml',
                content_type="text/xml",
                size=len(xml.getvalue()),
                charset='UTF-8')
        autor = 1 if request.user not in User.objects.all() else request.user
        dest_cnpj = mydoc.getElementsByTagName('dest')[0].getElementsByTagName('CNPJ')[0].firstChild.nodeValue
        if dest_cnpj not in cnpjs:
            nf = mydoc.getElementsByTagName('nNF')[0].firstChild.nodeValue
            dhEmi = dateformat.format(datetime.datetime.strptime(mydoc.getElementsByTagName('dhEmi')[0].firstChild.nodeValue, '%Y-%m-%dT%H:%M:%S%z'), 'Y-m-d H:i')
            try:
                rem = mydoc.getElementsByTagName('emit')[0].getElementsByTagName('xFant')[0].firstChild.nodeValue
            except IndexError:
                rem = mydoc.getElementsByTagName('emit')[0].getElementsByTagName('xNome')[0].firstChild.nodeValue
            dest = mydoc.getElementsByTagName('dest')[0].getElementsByTagName('xNome')[0].firstChild.nodeValue
            dest_mun = mydoc.getElementsByTagName('dest')[0].getElementsByTagName('xMun')[0].firstChild.nodeValue
            dest_uf = mydoc.getElementsByTagName('dest')[0].getElementsByTagName('UF')[0].firstChild.nodeValue
            peso = mydoc.getElementsByTagName('transp')[0].getElementsByTagName('pesoB')[0].firstChild.nodeValue
            volume = mydoc.getElementsByTagName('transp')[0].getElementsByTagName('qVol')[0].firstChild.nodeValue
            vlr_nf = mydoc.getElementsByTagName('total')[0].getElementsByTagName('vNF')[0].firstChild.nodeValue
            skus = getText(mydoc)
            if skus:
                try:
                    rom = RomXML.objects.create(dt_emissao=dhEmi, nota_fiscal=nf, remetente=rem, destinatario=dest,
                    peso=peso, volume=volume, vlr_nf=vlr_nf, municipio=dest_mun, uf=dest_uf, autor=autor,
                                                xmlfile=file)
                except Exception as e:
                    print(f'Error: {e}, error_type: {type(e).__name__}')
                    raise e
                else:
                    for q in skus:
                        SkuRefXML.objects.create(codigo=q['sku'],desc_prod=q['descprod'],tp_un=q['un'], qnt_un=int(q['qnt']),
                                                 xmlref=rom)
            print('finalizado')
        else:
            pass
    return redirect('portaria:romaneioxml')

def getText(nodelist):
    doc = nodelist.getElementsByTagName('det')
    rc = []
    for q in doc:
        var1 = q.getElementsByTagName('prod')[0]
        sku = var1.getElementsByTagName('cProd')[0].firstChild.nodeValue
        descprod = var1.getElementsByTagName('xProd')[0].firstChild.nodeValue
        un = var1.getElementsByTagName('uTrib')[0].firstChild.nodeValue
        qnt = var1.getElementsByTagName('qTrib')[0].firstChild.nodeValue.split('.')[0]
        all = {'sku':sku, 'descprod':descprod, 'un':un, 'qnt':qnt}
        rc.append(all)
    return rc

def getFiles(*args):
    s = BytesIO()

    zf = ZipFile(s, 'w')
    for q in args:
        obj = get_object_or_404(RomXML, pk=q)
        file = os.path.join(settings.MEDIA_ROOT, str(obj.xmlfile))
        fdir, fname = os.path.split(file)
        zf.write(file, fname)
    zf.close()

    resp = HttpResponse(s.getvalue(), content_type="application/x-zip-compressed")
    resp['Content-Disposition'] = f'attachment; filename={datetime.datetime.today()}.rar'

    return resp

def romxmltoexcel(*romaneio, tp_dld):
    array = []
    roms = []
    for q in romaneio:
        if tp_dld == 'Completo':
            array.append({'nf':q.nf1, 'municipio':q.municipio1, 'uf':q.uf1, 'codigo':q.codigo1,
                          'qnt_un':q.qnt_un1, 'desc':q.desc_prod1, 'remetente':q.rem, 'ref_id':q.romaneio_id,
                          'volume':q.volume})
            if q.romaneio_id not in roms:
                roms.extend({q.romaneio_id})
        elif tp_dld == 'Simples':
            array.append({'nf': q.nf1, 'uf': q.uf1, 'volume': q.volume})
            if q.id not in roms:
                roms.extend({q.id})
        elif tp_dld == 'Remetente':
            array.append({'municipio': q.municipio1, 'uf': q.uf1, 'codigo': q.codigo1,
                          'qnt_un': q.qnt_un1, 'desc': q.desc_prod1, 'remetente': q.rem, 'nota': q.romaneio_id,
                          'volume': q.volume, 'valor': q.valor, 'tp_un':q.tp_un1, 'peso':q.peso})
            if q.romaneio_id not in roms:
                roms.extend({q.romaneio_id})
        elif tp_dld == 'Destinatario':
            array.append({'municipio': q.municipio1, 'uf': q.uf1, 'codigo': q.codigo1,
                          'qnt_un': q.qnt_un1, 'desc': q.desc_prod1, 'destinatario': q.dest, 'nota': q.romaneio_id,
                          'volume': q.volume, 'valor': q.valor, 'tp_un': q.tp_un1, 'peso': q.peso})
            if q.romaneio_id not in roms:
                roms.extend({q.romaneio_id})
    RomXML.objects.filter(pk__in=roms).update(printed=True)
    pdr = pd.DataFrame(array)
    if tp_dld == 'Completo':
        dt = (pdr.pivot_table(index=['codigo','desc'],
                             columns=['uf'],
                             values=['qnt_un'],
                             aggfunc=np.sum,
                             fill_value='0',
                             margins=True,
                             margins_name='Total')).astype(np.int64)
    elif tp_dld == 'Simples':
        dt = (pdr.pivot_table(index=['nf'],
                              columns=['uf'],
                              values=['volume'],
                              aggfunc=np.sum,
                              fill_value='0',
                              margins=True,
                              margins_name='Total')).astype(np.int64)
    elif tp_dld == 'Remetente':
        dt = (pdr.pivot_table(index=['remetente','nota','valor','peso','desc','tp_un',],
                              values=['qnt_un',],
                              fill_value='0')).astype(np.float)
    elif tp_dld == 'Destinatario':
        dt = (pdr.pivot_table(index=['destinatario', 'nota', 'volume', 'valor', 'peso', 'desc', 'tp_un', ],
                              values=['qnt_un', ],
                              fill_value='0')).astype(np.float)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{datetime.datetime.today()}.xlsx"'
    writer = pd.ExcelWriter(response, engine='xlsxwriter')
    dt.to_excel(writer, 'Dinamica')
    pdr.to_excel(writer, 'Relatorio')
    writer.save()
    try:
        return response
    except Exception as e:
        raise e
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
                Auxilio moradia: R$ {19:.2f}
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
             aux_moradia=Coalesce(Sum('nfservicopj__aux_moradia', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
             outros_cred=Coalesce(Sum('nfservicopj__outros_cred', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
             desc_convenio=Coalesce(Sum('nfservicopj__desc_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
             outros_desc=Coalesce(Sum('nfservicopj__outros_desc',filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
             ).annotate(total=(F('salario') + F('ajuda_custo') + F('faculdade') + F('cred_convenio') + F('outros_cred') + F('aux_moradia') ) - (F('adiantamento') + F('desc_convenio') + F('outros_desc')))
        arrya.extend(query)
    for q in arrya:
        try:
            send_mail(
                subject=title,
                message=text.format(
                    q.filial, q.nome, q.salario, q.faculdade, q.ajuda_custo, q.cred_convenio,
                    q.outros_cred, q.adiantamento, q.desc_convenio, q.outros_desc, q.total,
                    q.cpf_cnpj, q.banco, q.ag, q.conta, q.op, dt_1, dt_2, dt_pgmt, q.aux_moradia
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[q.email]
            )
            MailsPJ.objects.create(funcionario_id=q.id, data_pagamento=datetime.datetime.strptime(dt_pgmt,'%Y-%m-%d'),
                                   mensagem=text.format(
                    q.filial, q.nome, q.salario, q.faculdade, q.ajuda_custo, q.cred_convenio,
                    q.outros_cred, q.adiantamento, q.desc_convenio, q.outros_desc, q.total,
                    q.cpf_cnpj, q.banco, q.ag, q.conta, q.op, dt_1, dt_2, dt_pgmt, q.aux_moradia
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
    array = []
    date1 = request.POST.get('date1')
    date2 = request.POST.get('date2')
    palete = MovPalete.objects.filter(data_ult_mov__lte=date2, data_ult_mov__gte=date1)
    if palete:
        for q in palete:
            array.append({'origem':q.origem, 'destino':q.destino, 'data_ult_mov':q.data_ult_mov, 'placa':q.placa_veic,
                          'autor':q.autor, 'tipo':q.palete.tp_palete})
        df = pd.DataFrame(array)
        buffer = io.BytesIO(df.to_string().encode('utf-8'))
        df.to_excel(buffer, engine='xlsxwriter', index=False)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="teste.xlsx"'
        writer = pd.ExcelWriter(response, engine='xlsxwriter')
        df.to_excel(writer, 'sheet1', index=False)
        writer.save()
        return response
    else:
        messages.error(request, 'Não encontrado valores para esta data')
        return redirect('portaria:paleteview')


def get_manu_csv(request):
    array = []
    data1 = request.POST.get('dataIni')
    data2 = request.POST.get('dataFin')
    try:
        dateparse = datetime.datetime.strptime(data1, '%Y-%m-%d')
        dateparse1 = datetime.datetime.strptime(data2, '%Y-%m-%d')
    except ValueError:
        messages.error(request,'Por favor digite uma data válida')
        return redirect('portaria:manutencaofrota')
    else:

        manutencao = ManutencaoFrota.objects.all().filter(dt_entrada__gte=dateparse, dt_entrada__lte=dateparse1)
        for q in manutencao:
            array.append({'id':q.id,'veiculo':q.veiculo.prefixoveic,'motorista':q.motorista, 'tp_manu':q.tp_manutencao,
                          'local_manu':q.local_manu,'ult_manu':q.dt_ult_manutencao,'entrada':q.dt_entrada,
                          'inicio':q.dt_ini_manu,'saida':q.dt_saida,'dias_parado':q.dias_veic_parado, 'km':q.km_atual,
                          'filial':q.filial,'socorro':q.socorro,'prev_entrega':q.prev_entrega,'status':q.status,
                          'autor':q.autor.username})
        df = pd.DataFrame(array)
        buffer = io.BytesIO(df.to_string().encode('utf-8'))
        df.to_excel(buffer, engine='xlsxwriter', index=False)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{dateparse}-{dateparse1}.xlsx"'
        writer = pd.ExcelWriter(response, engine='xlsxwriter')
        df.to_excel(writer, 'sheet1', index=False)
        writer.save()
        return response

def retornoromcsv(request):
    array = []
    if request.method == 'POST':
        date1 = request.POST.get('date1')
        date2 = request.POST.get('date2')

        getnfs = RetornoEtiqueta.objects.filter(saida__gte=date1, saida__lte=date2)
        for q in getnfs:
            array.append({'nf':q.nota_fiscal, 'saida':q.saida})
        pdr = pd.DataFrame(array)
        pdr.set_index('nf', inplace=True)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{datetime.datetime.today()}.xlsx"'
        writer = pd.ExcelWriter(response, engine='xlsxwriter')
        pdr.to_excel(writer, 'sheet1')
        writer.save()
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
    array = []
    try:
        ini = datetime.datetime.strptime(request.POST.get('dataini'), '%Y-%m-%d').date()
        fim = datetime.datetime.strptime(request.POST.get('datafim'), '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Por favor digite uma data válida')
        return redirect('portaria:frota')
    else:
        query = ChecklistFrota.objects.filter(datachecklist__lte=fim,datachecklist__gte=ini)
        if query:
            for q in query:
                array.append({'id':q.idchecklist, 'emissao':q.datachecklist, 'placa':q.placaveic.prefixoveic,
                              'motorista':q.motoristaveic.nome,'filial':q.get_filial_display(), 'km anterior':q.kmanterior,
                              'km atual':q.kmatual,'horimetro':q.horimetro, 'autor':q.autor.username})
            df = pd.DataFrame(array)
            buffer = io.BytesIO(df.to_string().encode('utf-8'))
            df.to_excel(buffer, engine='xlsxwriter', index=False)
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{ini}-{fim}.xlsx"'
            writer = pd.ExcelWriter(response, engine='xlsxwriter')
            df.to_excel(writer, 'sheet1', index=False)
            writer.save()
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
    host = 'pop.kinghost.net' #get_secret('EHOST_MN') ########## alterar
    e_user = 'bora@bora.tec.br' #get_secret('EUSER_MN') ########## alterar
    e_pass = 'Bor@dev#123' #get_secret('EPASS_MN') ########## alterar
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
                        e_body = e_body.replace(q, new_cid)
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
                            e_body = e_body.replace(q, new_cid)
                #continue
            except Exception as e:
                 print(f'insert data -- ErrorType: {type(e).__name__}, Error: {e}')
            else:
                #salva no banco de dados
                form = EmailMonitoramento.objects.filter(email_id=e_ref.strip())
                if form.exists():
                    try:
                        tkt = TicketMonitoramento.objects.get(pk=form[0].tkt_ref_id)
                    except Exception as e:
                        print(f'1ErrorType: {type(e).__name__}, Error: {e}')
                    else:
                        if form[0].ult_resp is not None:
                            aa = '<hr>' + e_body + '<p>Anterior</p><hr>' + form[0].ult_resp
                            bb = '<hr>' + e_from + ' -- ' + e_date + '<br>' + w_body + '<br>' + attatch + '<p>Anterior</p><hr>' + form[0].ult_resp_html
                        else:
                            aa = '<hr>' + e_body
                            bb = '<hr>' + e_from + ' -- ' + e_date + '<br>' + w_body + '<br>' + attatch
                        if tkt.status == 'ABERTO':
                            TicketMonitoramento.objects.filter(pk=form[0].tkt_ref_id).update(status='ANDAMENTO')
                        form.update(ult_resp=aa,ult_resp_html=bb, ult_resp_dt=e_date)
                        notify.send(sender=User.objects.get(pk=1), data=tkt.id, recipient=tkt.responsavel, verb='message',
                                    description=f"Você recebeu uma nova mensagem do ticket {tkt.id}")
                        pp.dele(i+1)
                else:
                    pp.dele(i + 1)
                    continue
    pp.quit()
    return redirect('portaria:monitticket')

def replymail_monitoramento(request, tktid, area, myfile):
    hoje = datetime.date.today()
    path = settings.STATIC_ROOT + '/monitoramento/' + str(hoje) + '/'
    media = ''
    attatch = ''
    rr = random.random()
    pattern = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp)')
    pattern2 = re.compile(r'/static/monitoramento/\S+(?i:jpeg|jpg|gif|png|bmp)')
    orig = get_object_or_404(EmailMonitoramento, tkt_ref_id=tktid)
    keyga = {v: k for k, v in TicketMonitoramento.GARAGEM_CHOICES}
    getmailfil = EmailOcorenciasMonit.objects.filter(rsocial=orig.tkt_ref.get_filial_display(), ativo=1)
    mailfil = ''
    for i in getmailfil:
        mailfil += i.email + ', '
    #send = orig.cc.split(';')
    send = ['IGOR.ROSARIO@BORA.COM.BR','ROBERT.DIAS@BORA.COM.BR', request.user.email] + orig.cc.split(',') + mailfil.split(',')
    if request.method == 'POST':
        msg1 = MIMEMultipart('related')
        msg = area
        msgm = area
        if myfile is not None:
            for q in myfile:
                locimg = os.path.join(path, str(q))
                if os.path.exists(os.path.join(path)):
                    fp = open(locimg, 'wb')
                    fp.write(q.read())
                    fp.close()
                    os.chmod(locimg, 0o777)
                    try:
                        os.rename(locimg, os.path.join(path, (str(rr) + str(q))))
                    except Exception as e:
                        os.rename(locimg, os.path.join(path, (str(rr) + str(q) + str(random.randint(1, 100)))))
                else:
                    os.mkdir(path=path)
                    os.chmod(path, 0o777)
                    fp = open(locimg, 'wb')
                    fp.write(q.read())
                    fp.close()
                    os.chmod(locimg, 0o777)
                    try:
                        os.rename(locimg, os.path.join(path, (str(rr) + str(q))))
                    except Exception as e:
                        os.rename(locimg, os.path.join(path, (str(rr) + str(q) + str(random.randint(1, 100)))))
                item = os.path.join('/static/monitoramento/' + str(hoje) + '/', (str(rr) + str(q)))
                aatt = '<div class="mailattatch"><a href="' + item + '" download><img src="/static/images/downicon.png" width="40"><p>' + str(q) + '</p></a></div>'
                attatch += aatt

                part = MIMEApplication(q.read(), name=str(q))
                part['Content-Disposition'] = 'attachment; filename="%s"' % q
                msg1.attach(part)
        if re.findall(pattern, msg):
            for q in re.findall(pattern, msg):
                media = q
                img_data = open(('/home/bora/www'+media),'rb').read()
                msgimg = MIMEImage(img_data, name=os.path.basename(media), _subtype='jpg')
                msgimg.add_header('Content-ID', f'{media}')
                msg1.attach(msgimg)
                msgm = msg.replace(('src="' + media + '"'), f'src="cid:{media}" ')
        sign = f'<br><img src="/static/images/macros-monit/{request.user}.jpg" width="600">'
        signimg = open(f'{settings.STATIC_ROOT}/images/macros-monit/{request.user}.jpg', 'rb').read()
        msgimg1 = MIMEImage(signimg, name=f'{request.user}.jpg', _subtype='jpg')
        msgimg1.add_header('Content-ID', f'{request.user}.jpg')
        msg1.attach(msgimg1)

        if orig.ult_resp:
            msgmail2222 = '<div class="container chmdimg">' + msgm + sign + '</div>' + orig.ult_resp.split('<p>Anterior</p><hr>')[0]
            msgmail1234 = '<div class="container chmdimg">' + msg + sign + '</div>' + orig.ult_resp_html.split('<p>Anterior</p><hr>')[0]
        else:
            msgmail2222 = '<div class="container chmdimg">' + msgm + sign + '</div>' + orig.mensagem
            msgmail1234 = '<div class="container chmdimg">' + msg + sign + '</div>' + orig.mensagem
        if re.findall(pattern2, msgmail2222):
            arrayzz = []
            for q in re.findall(pattern2, msgmail2222):
                fp = open(('/home/bora/www' + q), 'rb')
                img_data = fp.read()
                msgimg2 = MIMEImage(img_data, name=os.path.basename(q), _subtype='jpg')
                msgimg2.add_header('Content-ID', f'{os.path.basename(q)}')
                for i in msgimg2.walk():
                    if i['Content-ID'] not in arrayzz:
                        msg1.attach(msgimg2)  # causa dos attach pelas repetições duplicadas
                        msgmail2222 = msgmail2222.replace((f'="{q}"'), f'="cid:{os.path.basename(q)}"')
                        arrayzz.append(i['Content-ID'])
        msgmail2222 = msgmail2222.replace(f'<br><img src="/static/images/macros-monit/{request.user}.jpg" width="600">',f'<br><img src="cid:{request.user}.jpg" width="600">')
        msgmail1234 = msgmail1234.replace(f'<p>Anterior</p><hr>', '<hr>')
        msgmail2222 = msgmail2222.replace(f'<p>Anterior</p><hr>', '<hr>')

        if orig.ult_resp is not None:
            aa = msgm + sign + orig.ult_resp
            bb = '<hr>' + str(request.user) + ' -- ' + str(dateformat.format(timezone.now(), 'd-m-Y H:i')) + '<br>' + msgmail1234 + '<br>' + attatch + '<p>Anterior</p><hr>' + orig.ult_resp_html
        else:
            aa = msgm + sign
            bb = '<hr>' + str(request.user) + ' -- ' + str(dateformat.format(timezone.now(), 'd-m-Y H:i')) + '<br>' + msgmail1234 + '<br>' + attatch

        msg1['Subject'] = orig.assunto
        msg1['In-Reply-To'] = orig.email_id
        msg1['References'] = orig.email_id
        msg_id = make_msgid(idstring=None, domain='bora.com.br')
        msg1['Message-ID'] = msg_id
        msg1['From'] = get_secret('EUSER_MN')#############
        msg1['To'] = orig.cc
        msg1['CC'] = orig.cc
        msg1.attach(MIMEText(msgmail2222, 'html', 'utf-8'))
        smtp_p = '587'##############
        user = 'bora@bora.tec.br'##############
        try:
            print('entrou no try')
            sm = smtplib.SMTP(get_secret('EHOST_MN'), smtp_p)################
            #sm.set_debuglevel(1)
            sm.login(get_secret('EUSER_MN'), get_secret('EPASS_MN'))###############
            sm.sendmail(get_secret('EUSER_MN'), send, msg1.as_string())#############
            print('mandou o email')
            EmailMonitoramento.objects.filter(pk=orig.id).update(ult_resp=aa,ult_resp_html=bb, ult_resp_dt=dateformat.format(timezone.now(), 'Y-m-d H:i'))
        except Exception as e:
            print(f'ErrorType:{type(e).__name__}, Error:{e}')
        else:
            messages.success(request, 'Resposta enviada com sucesso!')

def createtktandmail(request, **kwargs):
    pattern = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp)')
    msg1 = MIMEMultipart('related')
    getmailfil = EmailOcorenciasMonit.objects.filter(rsocial=kwargs['filial'], ativo=1)
    mailfil = ''
    for i in getmailfil:
        mailfil += i.email+','
    #send = kwargs['cc'].split(';')
    send = ['IGOR.ROSARIO@BORA.COM.BR','ROBERT.DIAS@BORA.COM.BR', request.user.email] + kwargs['cc'].split(';') + mailfil.split(',')
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
            bb = '<hr>' + str(request.user) + ' -- ' + str(dateformat.format(timezone.now(), 'd-m-Y H:i')) + kwargs['msg']
            tkt = TicketMonitoramento.objects.create(nome_tkt=kwargs['assunto'], dt_abertura=timezone.now(),
                  responsavel=User.objects.get(username=kwargs['resp']), solicitante=request.user, remetente=kwargs['rem'],
                  destinatario=kwargs['dest'], cte=kwargs['cte'], status='ABERTO', categoria='Aguardando Recebimento',msg_id=msg_id,
                         filial=keyga[kwargs['filial']], tp_docto=kwargs['tp_docto'])
            mail = EmailMonitoramento.objects.create(assunto=kwargs['assunto'], mensagem=bb, cc=kwargs['cc'],
                                                     dt_envio=dateformat.format(timezone.now(), 'Y-m-d H:i'),
                                                     email_id=tkt.msg_id,tkt_ref_id=tkt.id)
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
    #Return all rows from a cursor as a dict
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def notifymanutencaovencidos():
    vencidos = ManutencaoFrota.objects.filter(status='ANDAMENTO')
    for q in vencidos:
        if q.prev_entrega < datetime.date.today():
            notify.send(User.objects.get(pk=1), recipient=q.autor, verb='message',
                        description=f"OS {q.id} vencida.")
        elif q.prev_entrega == datetime.date.today():
            notify.send(User.objects.get(pk=1), recipient=q.autor, verb='message',
                        description=f"OS {q.id} vence hoje!.")
        else:
            pass

def printetiquetas(array):
    print('iniciando impressao')
    if array:
        mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = get_secret('HOST_PRINT')
        port = int(get_secret('PORT_PRINT'))
        try:
            mysocket.connect((host, port))  # connecting to host
            for q in array:
                mysocket.send(q)  # using bytes
            mysocket.close()  # closing connection
        except Exception as e:
            print(f"Error:{e}, error_type:{type(e).__name__}")
        else:
            print('finalizou sem "erros"')

def mdfeporfilial(request):
    hoje = datetime.date.today()
    gachoices = GARAGEM_CHOICES
    mailchoices = {'SPO': [''],
                   'MG':  [''],
                   'TMA': [''],
                   'BMA': [''],
                   'BPE': [''],
                   'BPB': [''],
                   'BAL': [''],
                   'TCO': ['juliano.oliveira@borexpress.com.br', 'lino.loureiro@borexpress.com.br',
                           'rogeria.loureiro@borexpress.com.br'],
                   'VIX': ['mauricio@bora.com.br', 'ocorrenciavix@bora.com.br'],
                   'UDI': ['marcus.silva@borexpress.com.br', 'tulio.pereira@borexpress.com.br'],
                   'CTG': ['silvana.dily@borexpress.com.br', 'ygor.henrique@borexpress.com.br',
                           'fausto@borexpress.com.br'],
                   'MCZ': ['rafael@bora.com.br', 'elicarlos.santos@bora.com.br','valmir.silva@bora.com.br'],
                   'SSA': ['raphael.oliveira@bora.com.br', 'fernando.malaquias@bora.com.br',
                           'brandao.alan@bora.com.br'],
                   'NAT': ['ronnielly@bora.com.br', 'lindalva@bora.com.br', 'lidianne@bora.com.br'],
                   'SLZ': ['felipe@bora.com.br'],
                   'THE': ['felipe@bora.com.br'],
                   'BEL': ['felipe@bora.com.br'],
                   'VDC': ['jose.sousa@bora.com.br', 'fernando.sousa@bora.com.br'],
                   'REC': ['cinthya.souza@bora.com.br', 'patricia.santos@bora.com.br', 'edvanio.silva@bora.com.br',
                           'expedicao_rec@bora.com.br'],
                   'AJU': ['victor.hugo@bora.com.br'],
                   'JPA': ['patricia.lima@bora.com.br'],
                   'FOR': ['luciano@bora.com.br', 'erlandia@bora.com.br']
                   }
    for k, v in gachoices:
        result = mailchoices.get(v, '')
        conn = settings.CONNECTION
        cur = conn.cursor()
        cur.execute(f"""
                    SELECT DISTINCT
                           E5.CODIGO MDFE,
                           E5.DATA_SAIDA SAIDA_VEIC,
                           CASE
                               WHEN E5.DATA_CHEGADA <> '30/DEC/1899' THEN (TO_DATE(E5.DATA_CHEGADA,'DD-MM-YY HH24:MI:SS'))
                               WHEN E5.DATA_CHEGADA IS NULL AND E5.DT_PREVISAO = '30-DEC-1899' THEN NULL
                               WHEN E5.DATA_CHEGADA IS NULL THEN (TO_DATE(E5.DT_PREVISAO,'DD-MM-YY HH24:MI:SS'))
                           END CHEGADA_VEIC,
                           CASE
                               WHEN E5.ID_EMPRESA = '1' AND E5.ID_GARAGEM = '1' THEN 'SPO'
                               WHEN E5.ID_EMPRESA = '1' AND E5.ID_GARAGEM = '2'  THEN 'REC'
                               WHEN E5.ID_EMPRESA = '1' AND E5.ID_GARAGEM = '3'  THEN 'SSA'
                               WHEN E5.ID_EMPRESA = '1' AND E5.ID_GARAGEM = '4'  THEN 'FOR'
                               WHEN E5.ID_EMPRESA = '1' AND E5.ID_GARAGEM = '5'  THEN 'MCZ'
                               WHEN E5.ID_EMPRESA = '1' AND E5.ID_GARAGEM = '6'  THEN 'NAT'
                               WHEN E5.ID_EMPRESA = '1' AND E5.ID_GARAGEM = '7'  THEN 'JPA'
                               WHEN E5.ID_EMPRESA = '1' AND E5.ID_GARAGEM = '8'  THEN 'AJU'
                               WHEN E5.ID_EMPRESA = '1' AND E5.ID_GARAGEM = '9'  THEN 'VDC'
                               WHEN E5.ID_EMPRESA = '1' AND E5.ID_GARAGEM = '10' THEN 'MG'
                               WHEN E5.ID_EMPRESA = '1' AND E5.ID_GARAGEM = '50' THEN 'SPO'
                               WHEN E5.ID_EMPRESA = '1' AND E5.ID_GARAGEM = '20' THEN 'SPO'
                               WHEN E5.ID_EMPRESA = '1' AND E5.ID_GARAGEM = '21' THEN 'SPO'
                               WHEN E5.ID_EMPRESA = '2' AND E5.ID_GARAGEM = '20' THEN 'CTG'
                               WHEN E5.ID_EMPRESA = '2' AND E5.ID_GARAGEM = '21' THEN 'TCO'
                               WHEN E5.ID_EMPRESA = '2' AND E5.ID_GARAGEM = '22' THEN 'UDI'
                               WHEN E5.ID_EMPRESA = '2' AND E5.ID_GARAGEM = '23' THEN 'TMA'
                               WHEN E5.ID_EMPRESA = '2' AND E5.ID_GARAGEM = '24' THEN 'VIX'  
                               WHEN E5.ID_EMPRESA = '2' AND E5.ID_GARAGEM = '50' THEN 'VIX'
                               WHEN E5.ID_EMPRESA = '3' AND E5.ID_GARAGEM = '30' THEN 'BMA'
                               WHEN E5.ID_EMPRESA = '3' AND E5.ID_GARAGEM = '31' THEN 'BPE'
                               WHEN E5.ID_EMPRESA = '3' AND E5.ID_GARAGEM = '32' THEN 'BEL'    
                               WHEN E5.ID_EMPRESA = '3' AND E5.ID_GARAGEM = '33' THEN 'BPB'
                               WHEN E5.ID_EMPRESA = '3' AND E5.ID_GARAGEM = '34' THEN 'SLZ'
                               WHEN E5.ID_EMPRESA = '3' AND E5.ID_GARAGEM = '35' THEN 'BAL'
                               WHEN E5.ID_EMPRESA = '3' AND E5.ID_GARAGEM = '36' THEN 'THE'        
                           END FILIAL,
                           MO.NOME MOTORISTA,
                           VE.PREFIXOVEIC PLACA,
                           F1.CONHECIMENTO CTE,
                           F0.DT_PREV_ENTREGA LEADTIME,
                           E2.DESC_LOCALIDADE CIDADE,
                           E2.COD_UF UF,
                           F1.REM_RZ_SOCIAL REMETENTE,       
                           F1.DEST_RZ_SOCIAL DESTINATARIO,
                           F1.VOLUMES,
                           F1.PESO,
                           C1.DESCRICAO_PROD,
                           F1.OBSERVACAO
                    FROM
                           EXA025 E5,       
                           EXA026 E6,
                           FTA001 F1,
                           FTA011 F0,
                           FTA014 F4,
                           EXA002 E2,
                           CMA041 C1,
                           
                           BGM_MDF_ELETRONICO BG,
                           VWCGS_FUNCIONARIOSCOMAGREGADO MO,
                           FRT_CADVEICULOS VE
                    WHERE 
                           E5.RECNUM = BG.RECNUM_EXA025                     AND
                           
                           E5.RECNUM = E6.RECNUM_EXA025                     AND
                           
                           F1.EMPRESA = F0.EMPRESA                          AND
                           F1.FILIAL = F0.FILIAL                            AND
                           F1.GARAGEM = F0.GARAGEM                          AND
                           F1.SERIE = F0.SERIE                              AND
                           F1.CONHECIMENTO = F0.CONHECIMENTO                AND
                           
                           E6.EMPRESA = F1.EMPRESA                          AND
                           E6.FILIAL = F1.FILIAL                            AND
                           E6.GARAGEM = F1.GARAGEM                          AND
                           E6.SERIE_CTRC = F1.SERIE                         AND
                           E6.NUMERO_CTRC = F1.CONHECIMENTO                 AND                           
                                                      
                           F1.EMPRESA = F4.EMPRESA                          AND
                           F1.FILIAL = F4.FILIAL                            AND
                           F1.GARAGEM = F4.GARAGEM                          AND
                           F1.SERIE = F4.SERIE                              AND
                           F1.CONHECIMENTO = F4.CONHECIMENTO                AND
                           
                           F4.ITEM_GRUPO = C1.CODIGO                        AND 
                           
                           F1.LOCALID_ENTREGA = E2.COD_LOCALIDADE           AND
                           
                           E5.ID_MOTORISTA = MO.IDENTIFICACAO               AND
                           E5.MOTORISTA = MO.CODINTFUNC                     AND
                           E5.VEICULO = VE.CODIGOVEIC                       AND
                           
                           E5.GARAGEM IN (1,10,23,30)                       AND 
                           E5.ENTREGA_TRANSF = 'T'                          AND
                           E5.TIPO_DOCTO = '58'                             AND
                           
                           E5.ID_GARAGEM = {k}                              AND
                           E5.ID_GARAGEM <> 1                               AND
                           BG.STATUS = 'A'                                  AND
                           
                           BG.DATA_ENVIO BETWEEN ((SYSDATE)-1) AND (SYSDATE)
                    """)
        res = dictfetchall(cur)
        cur.close()
        pdr = pd.DataFrame(res)
        if not pdr.empty:
            send = ['renan.amarantes@bora.com.br', 'alan@bora.com.br', 'thiago@bora.com.br'] + result
            #Separa congelado inicio
            if k in ('6','7'):
                resultrec = mailchoices.get('REC', '')
                try:
                    row = pdr.loc[pdr['DESCRICAO_PROD'] == 'CONGELADO']
                except Exception as e:
                    print(f'Error:{e}, error_type:{type(e).__name__}')
                else:
                    pdr = pdr.drop(row.index)
                    if not row.empty:
                        send2 = ['renan.amarantes@bora.com.br', 'alan@bora.com.br', 'thiago@bora.com.br'] + resultrec
                        msg = MIMEMultipart('related')
                        msg['From'] = get_secret('EUSER_MN')
                        msg['To'] = '; '.join(send2)
                        msg['Subject'] = f'MDFEs por Filial: REC'
                        text = f'''Prezados,\n
                               Segue relação de MDFEs gerado pela matriz a caminho da filial REC.
                               \n
                               \n
                               Atenciosamente,\n
                               Bora Desenvolvimento.
                            '''
                        msg.attach(MIMEText(text, 'html', 'utf-8'))

                        buffer = io.BytesIO()
                        pd.ExcelWriter(buffer)
                        row['SAIDA_VEIC'] = pd.to_datetime(row['SAIDA_VEIC'], format='%d/%m/%Y').dt.strftime('%d/%m/%Y')
                        row['CHEGADA_VEIC'] = pd.to_datetime(row['CHEGADA_VEIC'], format='%d/%m/%Y').dt.strftime(
                            '%d/%m/%Y')
                        row['LEADTIME'] = pd.to_datetime(row['LEADTIME'], format='%d/%m/%Y').dt.strftime('%d/%m/%Y')
                        row.to_excel(buffer, engine='xlsxwriter', index=False)
                        part = MIMEApplication(buffer.getvalue(), name=v)
                        part['Content-Disposition'] = 'attachment; filename=%s.xlsx' % v

                        msg.attach(part)
                        try:
                            sm = smtplib.SMTP('smtp.bora.com.br', '587')
                            sm.set_debuglevel(1)
                            sm.login(get_secret('EUSER_MN'), get_secret('EPASS_MN'))
                            sm.sendmail(get_secret('EUSER_MN'), send2, msg.as_string())
                        except Exception as e:
                            raise e
                        # Separa congelado fim

            msg = MIMEMultipart('related')
            msg['From'] = get_secret('EUSER_MN')
            msg['To'] = '; '.join(send)
            msg['Subject'] = f'MDFEs por Filial: {v}'
            text = f'''Prezados,\n
                       Segue relação de MDFEs gerado pela matriz a caminho da filial {v}.
                       \n
                       \n
                       Atenciosamente,\n
                       Bora Desenvolvimento.
                    '''
            msg.attach(MIMEText(text, 'html', 'utf-8'))

            buffer = io.BytesIO()
            pd.ExcelWriter(buffer)
            pdr['SAIDA_VEIC'] = pd.to_datetime(pdr['SAIDA_VEIC'], format='%d/%m/%Y').dt.strftime('%d/%m/%Y')
            pdr['CHEGADA_VEIC'] = pd.to_datetime(pdr['CHEGADA_VEIC'], format='%d/%m/%Y').dt.strftime('%d/%m/%Y')
            pdr['LEADTIME'] = pd.to_datetime(pdr['LEADTIME'], format='%d/%m/%Y').dt.strftime('%d/%m/%Y')
            pdr.to_excel(buffer, engine='xlsxwriter', index=False)
            part = MIMEApplication(buffer.getvalue(), name=v)
            part['Content-Disposition'] = 'attachment; filename=%s.xlsx' % v

            msg.attach(part)
            try:
                sm = smtplib.SMTP('smtp.bora.com.br', '587')
                sm.set_debuglevel(1)
                sm.login(get_secret('EUSER_MN'), get_secret('EPASS_MN'))
                sm.sendmail(get_secret('EUSER_MN'), send, msg.as_string())
            except Exception as e:
                raise e
    return HttpResponse('<h3>Job finalizado!</h3>')

def bipagemdocrel(request):
    array = []
    if request.method == 'POST':
        date1 = request.POST.get('date1')
        date2 = request.POST.get('date2')
        fil = request.POST.get('fil')
        if date1 and date2 and fil and fil != 'Selecione...':
            date1 = datetime.datetime.strptime(request.POST.get('date1'), '%Y-%m-%d')
            date2 = datetime.datetime.strptime(request.POST.get('date2'), '%Y-%m-%d')
            query = EtiquetasDocumento.objects.filter(pub_date__lte=date2, pub_date__gte=date1, garagem=fil).annotate(
                total=Count('bipagemetiqueta'),user=F('bipagemetiqueta__autor__username'),
                pub=F('bipagemetiqueta__pub_date')
            )
            if query:
                for q in query:
                    array.append({'NR_DOC':q.nr_doc, 'GARAGEM':q.get_garagem_display(),
                                  'TP_DOC':q.get_tp_doc_display(), 'VOLUME':q.volume ,'NOTA':q.nota,
                                  'USER':q.user, 'DATA BIPAGEM':q.pub,'total':q.total})
                df = pd.DataFrame(array)
                buffer = io.BytesIO(df.to_string().encode('utf-8'))
                df.to_excel(buffer, engine='xlsxwriter', index=False)
                response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="{date1}-{date2}.xlsx"'
                writer = pd.ExcelWriter(response, engine='xlsxwriter')
                df.to_excel(writer, 'sheet1', index=False)
                writer.save()
                return response
            else:
                messages.error(request, 'Nao encontrado valores para esta data.')
        else:
            messages.error(request, 'Valores faltando, por favor verifique.')
    return redirect('portaria:etqrelatorio')

def bipagempalrel(request):
    array = []
    if request.method == 'POST':
        date1 = request.POST.get('date1')
        date2 = request.POST.get('date2')
        if date1 and date2:
            date1 = datetime.datetime.strptime(request.POST.get('date1'), '%Y-%m-%d').replace(hour=00, minute=00)
            date2 = datetime.datetime.strptime(request.POST.get('date2'), '%Y-%m-%d').replace(hour=23, minute=59)
            query = BipagemPalete.objects.filter(etq_ref__pub_date__lte=date2,etq_ref__pub_date__gte=date1).annotate(
                total=Count('cod_barras'))
            if query:
                for q in query:
                    array.append({'cliente':q.etq_ref.cliente, 'codigo':q.cod_barras, 'filial':q.get_filial_display(),
                                  'data_bipagem':q.bip_date, 'volume':q.volume_conf, 'autor':q.autor.username})
                df = pd.DataFrame(array)
                buffer = io.BytesIO(df.to_string().encode('utf-8'))
                df.to_excel(buffer, engine='xlsxwriter', index=False)
                response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="{date1}-{date2}.xlsx"'
                writer = pd.ExcelWriter(response, engine='xlsxwriter')
                df.to_excel(writer, 'sheet1', index=False)
                writer.save()
                return response
            else:
                messages.error(request, 'Nao encontrado valores para esta data.')
        else:
            messages.error(request, 'Valores faltando, por favor verifique.')
    return redirect('portaria:etqrelatorio')

def justificativa(request):
    gachoices = GARAGEM_CHOICES
    justchoices = JustificativaEntrega.JUSTIFICATIVA_CHOICES
    if request.method == 'GET':
        date1 = request.GET.get('data1')
        date2 = request.GET.get('data2')
        filial = request.GET.get('filial')
        if date1 and date2 and filial:
            form = JustificativaEntrega.objects.filter(id_garagem=filial, data_emissao__lte=date2, data_emissao__gte=date1,
                                                       cod_just__isnull=True, desc_just__isnull=True)
            return render(request,'portaria/etc/justificativa.html', {'form':form,'gachoices':gachoices,
                                                                      'justchoices':justchoices})
    if request.method == 'POST':
        lista = json.loads(request.POST.get('vals'))
        for q in lista:
            result = dict(justchoices).get(q['ocorr'])
            try:
                obj = get_object_or_404(JustificativaEntrega, pk=q['id'])
            except Exception as e:
                print(f'Error:{e}, error_type:{type(e).__name__}')
            else:
                JustificativaEntrega.objects.filter(pk=obj.id).update(cod_just=q['ocorr'], desc_just=result,
                                                                      autor=request.user)
        messages.success(request, 'Justificativas cadastradas')
        return HttpResponse('200')
    return render(request, 'portaria/etc/justificativa.html', {'gachoices': gachoices})

def rel_justificativa(request):
    gachoices = GARAGEM_CHOICES
    if request.method == 'POST':
        if 'pivot_rel_just' in request.POST:
            date1 = request.POST.get('date1')
            date2 = request.POST.get('date2')
            try:
                response = pivot_rel_just(date1=date1, date2=date2)
            except Exception as e:
                print(f'Error: {e}, error_type:{type(e).__name__}')
            else:
                return response
    return render(request, 'portaria/etc/rel_justificativa.html', {'gachoices': gachoices})

async def get_justificativas(request):
    conn = settings.CONNECTION
    cur = conn.cursor()
    cur.execute(f"""
                    SELECT 
                           F1.EMPRESA,
                           F1.FILIAL,
                           F1.GARAGEM,
                           F1.ID_GARAGEM, 
                           DECODE(F1.TIPO_DOCTO, 8, 'NFS', 'CTE') TP_DOC,
                           F1.CONHECIMENTO,
                           F1.DATA_EMISSAO,
                           F1.DATA_ENTREGA,
                           CASE
                               WHEN F1.TIPO_DOCTO = 8 THEN TO_CHAR(BC.NFANTASIACLI)
                               WHEN F1.TIPO_DOCTO = 57 THEN F1.REM_RZ_SOCIAL
                           END REMETENTE,
                           CASE 
                                WHEN F1.TIPO_DOCTO = 8 THEN F11.REC_RZ_SOCIAL
                                WHEN F1.TIPO_DOCTO = 57 THEN F1.DEST_RZ_SOCIAL
                           END DESTINATARIO,
                           F1.PESO,
                           CASE
                               WHEN F11.DT_PREV_ENTREGA IS NULL THEN '01-JAN-0001'
                               WHEN F11.DT_PREV_ENTREGA IS NOT NULL THEN TO_CHAR(F11.DT_PREV_ENTREGA, 'DD-MM-YYYY') 
                           END DT_PREV_ENTREGA,
                           CASE 
                                WHEN (TRUNC((MIN(F11.DT_PREV_ENTREGA))-(SYSDATE))*-1) >= 0 THEN (TRUNC((MIN(F11.DT_PREV_ENTREGA))-(SYSDATE))*-1)
                                WHEN (TRUNC((MIN(F11.DT_PREV_ENTREGA))-(SYSDATE))*-1) < 0 THEN 0
                           END EM_ABERTO_APOS_LEAD_TIME,
                           E2.DESC_LOCALIDADE || '-' || E2.COD_UF DESTINO,
                           LISTAGG ((LTRIM (F4.NOTA_FISCAL,0)), ' / ') NF                           
                    FROM 
                         FTA001 F1,
                         FTA011 F11,
                         EXA002 E2,
                         FTA004 F4,
                         BGM_CLIENTE BC               
                    WHERE
                         F1.LOCALID_ENTREGA = E2.COD_LOCALIDADE AND
                         F1.CLIENTE_FAT = BC.CODCLI             AND
                         
                         F1.EMPRESA = F11.EMPRESA               AND
                         F1.FILIAL = F11.FILIAL                 AND
                         F1.GARAGEM = F11.GARAGEM               AND
                         F1.SERIE = F11.SERIE                   AND
                         F1.CONHECIMENTO = F11.CONHECIMENTO     AND
                         
                         F1.EMPRESA = F4.EMPRESA                AND
                         F1.FILIAL = F4.FILIAL                  AND
                         F1.GARAGEM = F4.GARAGEM                AND
                         F1.CONHECIMENTO = F4.CONHECIMENTO      AND
                         F1.SERIE = F4.SERIE                    AND
                                                                           
                         F1.DATA_EMISSAO BETWEEN ((SYSDATE)-3) AND (SYSDATE)                         
                    GROUP BY
                           F1.EMPRESA,
                           F1.FILIAL,
                           F1.GARAGEM,
                           F1.ID_GARAGEM,
                           F1.TIPO_DOCTO,
                           BC.NFANTASIACLI,
                           F11.REC_RZ_SOCIAL,  
                           F1.CONHECIMENTO,
                           F1.DATA_EMISSAO,
                           F1.DATA_ENTREGA,
                           F1.REM_RZ_SOCIAL,
                           F1.DEST_RZ_SOCIAL,
                           F1.PESO,
                           F11.DT_PREV_ENTREGA,
                           E2.DESC_LOCALIDADE,
                           E2.COD_UF                         
                    """)
    res = dictfetchall(cur)
    print('query feita')
    cur.close()
    for i in res:
        try:
            await insert_to_justificativa(i)
        except Exception as e:
            print(f'Error:{e}, error_type:{type(e).__name__}')
            continue
    return HttpResponse('job done')

@sync_to_async
def insert_to_justificativa(obj):
    print(obj)
    nobj = JustificativaEntrega.objects.get_or_create(
        empresa=obj['EMPRESA'], filial=obj['FILIAL'], garagem=obj['GARAGEM'], id_garagem=obj['ID_GARAGEM'],
        conhecimento=obj['CONHECIMENTO'], data_emissao=obj['DATA_EMISSAO'], destinatario=obj['DESTINATARIO'],
        remetente=obj['REMETENTE'], peso=obj['PESO'], tipo_doc=obj['TP_DOC'],data_entrega=obj['DATA_ENTREGA'],
        lead_time=datetime.datetime.strptime(obj['DT_PREV_ENTREGA'], '%d-%m-%Y'),
        em_aberto=obj['EM_ABERTO_APOS_LEAD_TIME'], local_entreg=obj['DESTINO'], nota_fiscal=obj['NF']
    )

async def get_ocorrencias(request):
    conn = settings.CONNECTION
    cur = conn.cursor()
    cur.execute(f"""
                    SELECT 
                           A1.EMPRESA,
                           A1.FILIAL,
                           A1.GARAGEM,
                           A1.NUMERO_CTRC,
                           A1.TIPO_DOCTO,
                           A2.CODIGO,
                           A2.DESCRICAO,
                           A1.DATA_OCORRENCIA      
                    FROM 
                         ACA001 A1,
                         ACA002 A2
                    WHERE
                         A1.COD_OCORRENCIA = A2.CODIGO                    AND
                         A1.DATA_CADASTRO BETWEEN ((SYSDATE)-3) AND (SYSDATE)                        
                    """)
    res = dictfetchall(cur)
    print('query feita')
    cur.close()
    for i in res:
        try:
            await insert_to_ocorrencias(i)
        except Exception as e:
            print(f'Error:{e}, error_type:{type(e).__name__}')
            continue

@sync_to_async
def insert_to_ocorrencias(obj):
    print(obj)
    just = JustificativaEntrega.objects.filter(empresa=obj['EMPRESA'], filial=obj['FILIAL'], garagem=obj['GARAGEM'],
                                               conhecimento=obj['NUMERO_CTRC'])
    if just:
        nobj = OcorrenciaEntrega.objects.get_or_create(
            empresa=obj['EMPRESA'], filial=obj['FILIAL'], garagem=obj['GARAGEM'], conhecimento=obj['NUMERO_CTRC'],
            tp_doc=obj['TIPO_DOCTO'], cod_ocor=obj['CODIGO'], desc_ocor=obj['DESCRICAO'],
            data_ocorrencia=obj['DATA_OCORRENCIA'], entrega=just[0]
        )
    
def pivot_rel_just(date1, date2):
    array = []
    gachoices = GARAGEM_CHOICES
    dictga = {k:v for k,v in gachoices}
    compare_date = datetime.datetime.strptime('0001-01-01', '%Y-%m-%d')
    qs = JustificativaEntrega.objects.filter(data_emissao__lte=date2, data_emissao__gte=date1).exclude(garagem=1)
    for q in qs:
        array.append({'ID_GARAGEM':dictga[q.id_garagem],'CONHECIMENTO':q.conhecimento, 'DATA_EMISSAO':q.data_emissao,
                      'REMETENTE':q.remetente,'PESO':q.peso, 'LEAD_TIME':q.lead_time, 'EM_ABERTO':q.em_aberto,
                      'LOCAL_ENTREGA':q.local_entreg,'NOTA_FISCAL':q.nota_fiscal, 'COD_JUST':q.cod_just,
                      'DESC_JUST':q.desc_just, 'AUTOR':q.autor,
                      'DATA_ENTREGA': 'NAO ENTREGUE' if q.data_entrega == compare_date.date() else q.data_entrega
                      })
    pdr = pd.DataFrame(array)
    buffer = io.BytesIO(pdr.to_string().encode('utf-8'))
    pdr.to_excel(buffer, engine='xlsxwriter', index=False)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=relatorio-justificativa{datetime.date.today()}.xlsx'
    writer = pd.ExcelWriter(response, engine='xlsxwriter')
    pdr.to_excel(writer, 'sheet1', index=False)
    writer.save()
    return response

async def get_xmls_api(request):
    host = get_secret('EHOST_MN')
    user = get_secret('ESEND_MN')
    pasw = get_secret('EPASS_MN')
    
    pp = poplib.POP3(host)
    pp.set_debuglevel(1)
    pp.user(user)
    pp.pass_(pasw)
    xmlsarray = []
    num_messages = len(pp.list()[1])
    for i in range(num_messages):
        raw_email = b'\n'.join(pp.retr(i+1)[1])
        parsed_mail = email.message_from_bytes(raw_email)
        if parsed_mail.is_multipart():
            for part in parsed_mail.walk():
                filename = part.get_filename()
                if re.findall(re.compile(r'\w+(?i:.xml|.XML)'), str(filename)):
                    xmlsarray.extend({part.get_payload(decode=True)})
        pp.dele(i+1)
    pp.quit()
    await entradaxml(request, args=xmlsarray)
    return HttpResponse('done')

class TestApi:
    def __init__(self):
        self.__token = 'Bearer eyJhbGciOiJodHRwOi8vd3d3LnczLm9yZy8yMDAxLzA0L3htbGRzaWctbW9yZSNobWFjLXNoYTUxMiIsInR5cCI6IkpXVCJ9.eyJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3VzZXJkYXRhIjoiYnd1T3Q2RnRXN0p5L3lKQnh3QUhENXhQK2tJRk1BalpJWDFYQjRNQ1FUU2g4cjM0QU9rN2Jhd2hvVXJwSVhObyROYkUwcjh1dmZ1bmJLWm1XQVVsdWR3PT0iLCJpc3MiOiJBdXRoQVBJIiwiYXVkIjoiSW50ZWdyYXdheSJ9.u3Ikt1Tn-8j-zJuarsBE7zcHz9DRfQ6GGe7m_y5Olp4nPl8dMaft4V8qL5ptoLO220aCX_b2hcwNdwgElQMC8Q'
        self.url = f'https://wayds.net:8081/integraway/api/v1/pedido/status?pedido=0000008780&entrega=11099025'

    def conn(self):
        url = self.url
        token = self.__token
        response = requests.get(url, headers={'Authorization':token})

        return HttpResponse(response.json())