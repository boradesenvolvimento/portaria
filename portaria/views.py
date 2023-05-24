#edimports geral
import asyncio
import io
import ipdb
import json
import random
import csv
import datetime
import email, smtplib
import os
import re
import time
import socket
import tempfile
import textwrap
import poplib
import imaplib
from collections import Counter
from email.mime.base import MIMEBase
from io import BytesIO
from zipfile import ZipFile
from fpdf import FPDF
#from barcode import EAN13
from barcode.writer import ImageWriter

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
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
#from reportlab.pdfgen import canvas
#imports django built-ins
from PIL import Image
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.handlers.wsgi import WSGIRequest
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models.query import QuerySet, Prefetch
from django.db.models import Count, Sum, F, Q, Value, Subquery, CharField, ExpressionWrapper, IntegerField, \
    DateTimeField, Case, When
from django.db.models.functions import Coalesce, TruncDate, Cast, TruncMinute, Lower
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest, Http404, FileResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.defaultfilters import upper
from django.urls import reverse
from django.utils import timezone, dateformat
from django.views import generic
from xml.dom import minidom

from xlsxwriter import Workbook
from cx_Oracle import DatabaseError as cxerr

from envia_email import envia_email
#imports django projeto
from .dbtest import conndb
from .models import * #Cadastro, PaletControl, ChecklistFrota, Veiculos, NfServicoPj
from .forms import * #CadastroForm, isPlacaForm, DateForm, FilterForm, TPaletsForm, TIPO_GARAGEM, ChecklistForm
from .serializers import *
from mysite.settings import get_secret

# Gerador de código de barras
from barcode import Code39, EAN13


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

def paleteview(request):
    keyga = {k:v for k,v in GARAGEM_CHOICES}
    tp_fil = GARAGEM_CHOICES
    tp_fil.pop()
    tp_emp = Cliente.objects.values_list('razao_social', flat=True)
    form = PaleteControl.objects.values('loc_atual').\
        annotate(pbr=Count('id', filter=Q(tp_palete='PBR')),chep=Count('id', filter=Q(tp_palete='CHEP'))).\
        annotate(total=ExpressionWrapper(Count('id'), output_field=IntegerField())).exclude(Q(loc_atual='MOV'))
    ttcount = form.aggregate(total_amount=Sum('total'))
    fil = request.GET.get('filial')
    if fil:
        form = PaleteControl.objects.filter(loc_atual=keyga[fil]).values('loc_atual').\
            annotate(pbr=Count('id', filter=Q(tp_palete='PBR')),chep=Count('id', filter=Q(tp_palete='CHEP'))).\
            annotate(total=ExpressionWrapper(Count('id'), output_field=IntegerField()))
        ttcount = form.aggregate(total_amount=Sum('total'))
    return render(request, 'portaria/palete/paletes.html', {'form':form,'tp_fil':tp_fil,'tp_emp':tp_emp,
                                                            'ttcount':ttcount})

def cadpaletes(request):
    tp_emp = Cliente.objects.all().order_by('razao_social')
    filiais = Filiais.objects.all()
    if request.method == 'POST':
        qnt = request.POST.get('qnt')
        fil = request.POST.get('fil')
        emp = request.POST.get('emp') # Razao Social
        tp_p = request.POST.get('tp_p')
        if qnt and fil and emp and tp_p:
            try:
                int(qnt)
            except ValueError:
                messages.error(request,'Por favor digite um valor numérico para quantidade')
                return redirect('portaria:cadpaletes')
            else:
                nsal = Cliente.objects.filter(razao_social=emp).annotate(saldonew=Sum(F('saldo')+int(qnt)))
                Cliente.objects.filter(razao_social=emp).update(saldo=nsal[0].saldonew)
                for x in range(0,int(qnt)):

                    PaleteControl.objects.create(loc_atual=fil, tp_palete=tp_p, autor=request.user)
                    if x == 2000: break
                messages.success(request, f'{qnt} Paletes foram cadastrados com sucesso')
    return render(request, 'portaria/palete/cadpaletes.html', {'filiais':filiais, 'tp_emp':tp_emp})

def paletecliente(request):
    form = Cliente.objects.filter(~Q(saldo=0), intex='CLIENTE').order_by('razao_social')
    tcount = form.aggregate(total=Sum('saldo'))
    return render(request, 'portaria/palete/paletecliente.html', {'form':form,'tcount':tcount})

def saidapalete(request):
    tp_fil = GARAGEM_CHOICES
    tp_emp = Cliente.objects.all().order_by('razao_social')
    keyga = {k: v for k, v in GARAGEM_CHOICES}
    if request.method == 'POST':
        qnt = int(request.POST.get('qnt'))
        fil = str(request.POST.get('fil'))
        emp = request.POST.get('emp')
        tp_p = request.POST.get('tp_p')
        if qnt and fil and emp and tp_p:
            chk = Cliente.objects.get(razao_social=emp)
            Cliente.objects.filter(razao_social=emp).update(saldo=(chk.saldo - qnt))
            for q in range(0,qnt):
                PaleteControl.objects.filter(loc_atual=keyga[fil], tp_palete=tp_p).first().delete()
            messages.success(request, 'Saidas cadastradas com sucesso')
            return redirect('portaria:paletecliente')
    return render(request, 'portaria/palete/saidapalete.html', {'tp_fil':tp_fil,'tp_emp':tp_emp})

@login_required
def frota(request):
    form = ChecklistFrota.objects.all()
    motoristas = Motorista.objects.all()
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
            return render(request, 'portaria/frota/frota.html',{'form':form, 'motos':motoristas})
        elif mot and not pla:
            messages.error(request, 'Insira a placa')
            return render(request, 'portaria/frota/frota.html',{'form':form, 'motos':motoristas})
    return render(request, 'portaria/frota/frota.html',{'form':form, 'motos':motoristas})

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
    allfuncs = FuncPj.objects.filter(ativo=True).order_by('nome')
    form = FuncPjForm
    func = request.GET.get('func')
    if func:
        getid = get_object_or_404(FuncPj, pk=func)
        form = FuncPjForm(instance=getid)
        if request.method == 'POST':
            form = FuncPjForm(request.POST or None, instance=getid)
            if form.is_valid():
                if form.instance.pk:
                    form.save()

                messages.success(request, 'Entrada cadastrada com sucesso.')
                return redirect('portaria:atualizarfunc')
            else:
                messages.error(request, 'Algo deu errado, por favor contate seu administrador.')
                return redirect('portaria:index')
    return render(request, 'portaria/pj/atualizarfunc.html', {'fields': form, 'allfuncs': allfuncs, 'func': func})

@login_required
def servicospj(request):
    func = request.GET.get('nomefunc')
    filter = request.GET.get('filter')

    # nfs = NfServicoPj.objects.all().values('funcionario_id').distinct()
    # nfs_fun = [nf['funcionario_id'] for nf in nfs]

    if func:
        qnt_funcs = FuncPj.objects.filter(nome__icontains=func, ativo=True)
    elif filter:
        qnt_funcs = FuncPj.objects.all().filter(ativo=True).order_by(filter)
    else:
        qnt_funcs = FuncPj.objects.filter(ativo=True).order_by('nome')

    return render(request, 'portaria/pj/servicospj.html', {'qnt_funcs': qnt_funcs})

def inserirmesmovalores(request, id):
    if id:
        try:
            funcionario = get_object_or_404(FuncPj, pk=id)
            nf = NfServicoPj.objects.filter(funcionario=funcionario).order_by("-id").first()

            nf.data_pagamento += relativedelta(months=1)
            objeto = {
                "faculdade": nf.faculdade,
                "cred_convenio": nf.cred_convenio,
                "aux_moradia": nf.aux_moradia,
                "outros_cred": nf.outros_cred,
                "desc_convenio": nf.desc_convenio,
                "outros_desc": nf.outros_desc,
                "data_pagamento": nf.data_pagamento,
                "data_emissao": datetime.date.today(),
                "funcionario": funcionario,
            }

            objeto["autor"] = request.user

            NfServicoPj.objects.create(**objeto)
            messages.success(request, "Mesmo valor inserido com sucesso")
        except Exception as e:
            messages.error(request, "Nenhum valor foi inserido anteriormente.")

    return redirect('portaria:servicospj')

@login_required
def consultanfpj(request):
    array = []
    qnt_funcs = FuncPj.objects.filter(ativo=True)
    for q in qnt_funcs:
        nf = NfServicoPj.objects.filter(funcionario_id=q.id).order_by('-id')

        if len(nf) > 0:
            query = FuncPj.objects.filter(pk=q.id).annotate(
                faculdade=Coalesce(nf[0].faculdade,Value(0.0)),
                cred_convenio=Coalesce(nf[0].cred_convenio,Value(0.0)),
                outros_cred=Coalesce(nf[0].outros_cred,Value(0.0)),
                aux_moradia=Coalesce(nf[0].aux_moradia,Value(0.0)),
                desc_convenio=Coalesce(nf[0].desc_convenio,Value(0.0)),
                outros_desc=Coalesce(nf[0].outros_desc,Value(0.0)),
                ) \
                .annotate(total=((F('salario') + F('ajuda_custo') + F('faculdade') + F('cred_convenio') + F('outros_cred') + F('aux_moradia')) - (F('adiantamento') + F('desc_convenio') + F('outros_desc'))))
        else:
            query = FuncPj.objects.filter(pk=q.id).annotate(
                faculdade=Coalesce(Sum('nfservicopj__faculdade', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
                cred_convenio=Coalesce(Sum('nfservicopj__cred_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
                outros_cred=Coalesce(Sum('nfservicopj__outros_cred', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
                aux_moradia=Coalesce(Sum('nfservicopj__aux_moradia',filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
                desc_convenio=Coalesce(Sum('nfservicopj__desc_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
                outros_desc=Coalesce(Sum('nfservicopj__outros_desc', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
                ) \
                .annotate(total=((F('salario') + F('ajuda_custo') + F('faculdade') + F('cred_convenio') + F('outros_cred') + F('aux_moradia')) - (F('adiantamento') + F('desc_convenio') + F('outros_desc'))))
        array.extend(query)
    return render(request, 'portaria/pj/consultanfpj.html', {'array': array})

@login_required
def cadservicospj(request, args):
    func = get_object_or_404(FuncPj, pk=args)
    nf = NfServicoPj.objects.filter(funcionario_id=args).order_by("-id")
    autor = request.user

    if request.method == 'POST':
        form = ServicoPjForm(request.POST or None)
        if form.is_valid():
            calc = form.save(commit=False)
            calc.funcionario = func
            calc.autor = autor
            calc.save()
            messages.success(request, f'Valores cadastrados com sucesso para {calc.funcionario}')
            return HttpResponseRedirect(reverse('portaria:servicospj'))
    
    if len(nf) > 0:
        form = ServicoPjForm(instance=nf[0])
    else:
        form = ServicoPjForm()

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

def bonuspj(request):
    return render(request,'portaria/pj/bonuspj.html')

def bonuscadpj(request):
    form = BonusPJForm
    if request.method == 'POST':
        form = BonusPJForm(request.POST or None)
        if form.is_valid():
            bonus = form.save(commit=False)
            bonus.autor = request.user
            bonus.save()
            
            messages.success(request, 'Cadastrado com sucesso!')
            return redirect('portaria:bonuspj')
        messages.error(request, 'Ocorreu erro ao cadastrar!')

    return render(request,'portaria/pj/bonuscadpj.html', {'form':form})

def bonusviewpj(request):
    hoje = datetime.date.today()
    nome = request.POST.get('textbox')
    option = request.POST.get('option')
    mostrar = True

    order_by = "data_pagamento"
    filter = {
        "cancelado": False
    }

    if nome:
        filter['funcionario__nome__contains'] = nome
    if option == "Quitado":
        filter['quitado'] = True
        mostrar = False
    else:
        filter['quitado'] = False
    if option == "Bônus vencido":
        filter['data_pagamento__lte'] = hoje
    if option == "Próximos do vencimento":
        filter['data_pagamento__gte'] = hoje

    bonus = BonusPJ.objects.filter(**filter).order_by(order_by)

    return render(request, 'portaria/pj/bonusviewpj.html', {'bonus': bonus, 'mostrar': mostrar})

def bonusquit(request, idbpj):
    bonus = get_object_or_404(BonusPJ, pk=idbpj)
    try:
        BonusPJ.objects.filter(pk=bonus.id).update(quitado=True, data_quitacao=timezone.now())
    except ObjectDoesNotExist:
        messages.error(request, 'Erro')
        return redirect('portaria:bonusviewpj')
    else:
        messages.success(request, f'Férias quitadas para o funcionário {bonus.funcionario.nome}')
        return redirect('portaria:bonusviewpj')
    
def contratopj(request):
    return render(request,'portaria/pj/contratopj.html')

def contratocadpj(request):
    if request.method == 'POST':
        form = ContratoPJForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                contrato = form.save(commit=False)
                contrato.autor = request.user
                contrato.save()

                messages.success(request, 'Cadastrado com sucesso!')
                return redirect('portaria:contratopj')
            messages.error(request, 'Formulário inválido')
        except Exception as e:
            messages.error(request, 'Ocorreu erro ao cadastrar!')
    else:        
        form = ContratoPJForm()

    return render(request,'portaria/pj/contratocadpj.html', {'form':form})

def contratoviewpj(request):
    hoje = datetime.date.today()
    nome = request.POST.get('textbox')
    option = request.POST.get('option')

    order_by = "funcionario__nome"
    filter = {}

    if nome:
        filter['funcionario__nome__contains'] = nome
    if option == "Bônus vencido":
        filter['data_pagamento__lte'] = hoje
    if option == "Próximos do vencimento":
        filter['data_pagamento__gte'] = hoje

    contratos = ContratoPJ.objects.filter(**filter).order_by(order_by)

    return render(request, 'portaria/pj/contratoviewpj.html', {'contratos': contratos})

def contratoeditarpj(request, idcpj):
    contrato = get_object_or_404(ContratoPJ, id=idcpj)
    
    if request.method == 'POST':
        form = ContratoPJForm(request.POST, instance=contrato)
        if form.is_valid():
            try:
                form.save()
            except Exception:
                messages.error(request, 'Algo deu errado, com o servidor.')
            finally:
                messages.success(request, 'Contrato editado com sucesso.')
                return redirect('portaria:contratoviewpj')
        else:
            messages.error(request, 'Dados do Formulário inválido.')
            return redirect('portaria:contratoeditarpj', idcpj=idcpj)
    else:
        form = ContratoPJForm(instance=contrato)

    return render(request, 'portaria/pj/contratoeditarpj.html', {'form': form})

def get_contrato_csv(request):
    hoje = datetime.date.today()
    try:
        ini = datetime.datetime.strptime(request.POST.get('dataini'), '%Y-%m-%d').date()
        fim = datetime.datetime.strptime(request.POST.get('datafim'), '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Por favor, digite uma data válida')
        return redirect('portaria:contratopj')
    else:
        response = HttpResponse(content_type='text/csv',
                                headers={'Content-Disposition':f'attatchment; filename=contrato/{hoje.strftime("%d/%m")}.csv"'})
        response.write(u'\ufeff'.encode('utf8'))
        writer = csv.writer(response)
        writer.writerow([
            "id","funcionario","inicio_contrato","final_contrato", "data_reajuste",
            "valor_reajuste", "anexo", "observacao", "data_criacao", "autor"
        ])

        contrato = ContratoPJ.objects.all().values_list(
            "id","funcionario","inicio_contrato","final_contrato", "data_reajuste",
            "valor_reajuste", "anexo", "observacao", "data_criacao", "autor"
        ).filter(data_reajuste__gte=ini,data_reajuste__lte=fim)

        for linha in contrato:
            writer.writerow(linha)

    return response

def feriasview(request):
    hoje = datetime.date.today()
    dias = hoje + datetime.timedelta(days=60)
    aa = FuncPj.objects.filter(ativo=True).values_list('id', flat=True)
    ferias = feriaspj.objects.filter(quitado=False, funcionario_id__in=aa).order_by('vencimento')
    nome = request.POST.get('textbox')
    option = request.POST.get('option')

    order_by = "vencimento"
    filter = {}

    if nome:
        filter['funcionario__nome__contains'] = nome
    if option == "Quitado":
        filter['quitado'] = True
    else:
        filter['quitado'] = False
    if option == "Bônus vencido":
        filter['vencimento__lte'] = hoje
    if option == "Próximos do vencimento":
        filter['vencimento__gte'] = hoje

    ferias = feriaspj.objects.filter(**filter).order_by(order_by)


    return render(request, 'portaria/pj/feriasview.html', {'ferias': ferias, 'dias':dias, 'hoje':hoje})

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
            messages.error(request, 'Por favor, digite uma data válida')
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
                    messages.error(request, 'Por favor, digite uma data válida')
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
def disponibilidade_frota(request: WSGIRequest) -> HttpResponse:
    if request.user.is_authenticated:
        hoje = datetime.date.today().strftime("%Y-%m-%d")
        filiais = [value for _, value in FILIAL_CHOICES]
        filial_selecionada = request.GET.get('filiais')

        veiculos: list[Veiculos] = list(Veiculos.objects.filter(filial=filial_selecionada).order_by('prefixoveic'))
        movimentos: list[DisponibilidadeFrota] = list(DisponibilidadeFrota.objects.filter(filial=filial_selecionada, data_preenchimento=hoje))

        placas = {movimento.placa for movimento in movimentos}

        bloqueio_parado = []
        bloqueio_preventivo = []
        for veiculo in veiculos:
            
            # Verificando qual foi o ultimo movimento do veiculo e bloqueando escolha
            movimento = veiculo.ultimo_dispo_frota
            if movimento:
                if movimento.status == "PARADO":
                    dias_restantes = (movimento.data_liberacao - datetime.date.today()).days
                    if dias_restantes >= 0: bloqueio_parado.append(veiculo)

                if movimento.status == "PREVENTIVO":
                    dias_restantes = (movimento.data_previsao - datetime.date.today()).days
                    if dias_restantes >= 0: bloqueio_preventivo.append(veiculo)
            
            # Transformando numero em um codigo
            veiculo.codigotpveic = Veiculos.CODIGOTPVEIC_CHOICES[int(veiculo.codigotpveic) - 1][1]
        
        if request.method == 'POST':
            dict: dict = request.POST.dict() #Transformando o request em dict
            cor: str = [*dict][1] # Selecionando a cor vinda do request 
            veiculo: Veiculos = Veiculos.objects.get(codigoveic=dict[cor]) # {'COR SELECIONADA': CODIGOVEIC}

            service = DisponibilidadeFrotaService()
            funcoes = {
                "vermelho": service.parado,
                "amarelo": service.preventivo,
                "verde": service.funcionando
            }

            resultado = funcoes[cor](request, veiculo)

            if not resultado:
                messages.error(request, 'Erro ao cadastrar Movimento')
            
            return HttpResponseRedirect(f'/frota/disponibilidade-frota?filiais={filial_selecionada}')

        return render(request, 'portaria/frota/disponibilidade_frota.html',
                    {'filiais': filiais, 'veiculos': veiculos, 'placas_movimentos': placas,
                     'filial': filial_selecionada, 'hoje': hoje,
                     'bloqueio_vermelho': bloqueio_parado,
                     'bloqueio_amarelo': bloqueio_preventivo})
    else:
        auth_message = 'Usuário não autenticado, por favor logue novamente'
        return render(request, 'portaria/portaria/cadastroentrada.html', {'auth_message': auth_message})

class DisponibilidadeFrotaService():
    @staticmethod
    def funcionando(request: WSGIRequest, veiculo: Veiculos) -> bool:
        movimento = {
            "placa": veiculo.prefixoveic,
            "filial": veiculo.filial,
            "status": "FUNCIONANDO",
            "data_preenchimento": datetime.date.today(),
            "autor_id": request.user.id,
        }

        return DisponibilidadeFrotaService.criar_movimento(movimento, veiculo) 

    @staticmethod
    def preventivo(request: WSGIRequest, veiculo: Veiculos) -> bool:
        dict = request.POST.dict()
        movimento = {
            "placa": veiculo.prefixoveic,
            "filial": veiculo.filial,
            "status": "PREVENTIVO",
            "data_preenchimento": datetime.date.today(),
            "data_previsao": dict.get('data_previsao') or datetime.date.today(),
            "observacao": dict.get('observacao'),
            "ordem_servico": dict.get('ordem_servico'),
            "autor_id": request.user.id,
        }

        return DisponibilidadeFrotaService.criar_movimento(movimento, veiculo)        

    @staticmethod
    def parado(request: WSGIRequest, veiculo: Veiculos) -> bool:
        dict = request.POST.dict()
        movimento = {
            "placa": veiculo.prefixoveic,
            "filial": veiculo.filial,
            "status": "PARADO",
            "data_preenchimento": datetime.date.today(),
            "data_liberacao": dict.get('data_liberacao') or datetime.date.today(),
            "observacao": dict.get('observacao'),
            "ordem_servico": dict.get('ordem_servico'),
            "autor_id": request.user.id,
        }

        return DisponibilidadeFrotaService.criar_movimento(movimento, veiculo)

    @staticmethod
    def criar_movimento(movimento: dict, veiculo: Veiculos):
        try:
            movimento_criado = DisponibilidadeFrota.objects.create(**movimento)

            veiculo.ultimo_dispo_frota = movimento_criado
            veiculo.save()

            return True
        
        except Exception as e:
            print(f"Erro ao criar DISPONIBILIDADE FROTA - {movimento.status}", e)
            return False


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
                conn = conndb()
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
                    modal = EmailOcorenciasMonit.objects.filter(rsocial=res[0]['remetente'], ativo=1)
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
        fis=Count('id', filter=Q(servico='FISCAL')), praxio=Count('id', filter=Q(servico='PRAXIO')),
        des=Count('id', filter=Q(servico='DESCARGA')), comp=Count('id', filter=Q(servico='COMPROVANTE')),
        hoje=Count('id', filter=Q(dt_abertura__date=datetime.date.today())),andamento=Count('id',
                                      filter=Q(status='ABERTO') | Q(status='ANDAMENTO'))
    ).aggregate(fis1=Sum('fis'), praxio1=Sum('praxio'), des1=Sum('des'), comp1=Sum('comp'), hoje1=Sum('hoje'),
                andamento1=Sum('andamento'))
    return render(request, 'portaria/chamado/chamado.html', {'metrics':metrics})

def chamadopainel(request):
    groups = request.user.groups.values_list('name', flat=True)
    form = TicketChamado.objects.all().exclude(Q(status='CANCELADO') | Q(status='CONCLUIDO'))
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
    catg = TicketChamado.CATEGORIA_CHOICES
    fil = GARAGEM_CHOICES
    resp = User.objects.filter(groups__name='chamado').exclude(id=1)
    form = get_object_or_404(EmailChamado, tkt_ref=tktid)
    editor = TextEditor()
    array = []
    try:
        for q in form.ult_resp_html.split('<p>Anterior</p><hr>'):
            array.append(q)
    except:
        pass
    if request.method == 'POST':
        ndptm = request.POST.get('ndptm')
        nstts = request.POST.get('nstts')
        nresp = request.POST.get('nresp')
        nfil = request.POST.get('nfil')
        area = request.POST.get('area')
        ncatg = request.POST.get('catg')
        nsubject = request.POST.get('subject')
        ncc = request.POST.get('mailcc')
        try:
            if nsubject != form.assunto:
                TicketChamado.objects.filter(pk=form.tkt_ref_id).update(nome_tkt=nsubject,
                                                                        ultimo_autor=request.user.username,
                                                                        ultima_att=timezone.now())
                form.assunto = nsubject
                form.save()
            if ncc != form.tkt_ref.solicitante:
                TicketChamado.objects.filter(pk=form.tkt_ref_id).update(solicitante=ncc,
                                                                        ultimo_autor=request.user.username,
                                                                        ultima_att=timezone.now())
            if ncatg != 'selected':
                TicketChamado.objects.filter(pk=form.tkt_ref_id).update(categoria=ncatg,
                                                                        ultimo_autor=request.user.username,
                                                                        ultima_att=timezone.now())
            if ndptm != 'selected':
                TicketChamado.objects.filter(pk=form.tkt_ref_id).update(departamento=ndptm,
                                                                        ultimo_autor=request.user.username,
                                                                        ultima_att=timezone.now())
            if nresp != 'selected':
                TicketChamado.objects.filter(pk=form.tkt_ref_id).update(responsavel=nresp,
                                                                        ultimo_autor=request.user.username,
                                                                        ultima_att=timezone.now())
            if nfil != 'selected':
                TicketChamado.objects.filter(pk=form.tkt_ref_id).update(filial=nfil,
                                                                        ultimo_autor=request.user.username,
                                                                        ultima_att=timezone.now())
            if nstts != 'selected':
                TicketChamado.objects.filter(pk=form.tkt_ref_id).update(status=nstts,
                                                                        ultimo_autor=request.user.username,
                                                                        ultima_att=timezone.now())
            if area and area != '<p><br></p>':
                if request.POST.get('file') != '':
                    myfile = request.FILES.getlist('file')
                else:
                    myfile = None
                try:
                    chamadoupdate(request, tktid, area, myfile)
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)
        else:
            messages.success(request, 'Alterações concluídas')
            return redirect('portaria:chamadopainel')
    return render(request, 'portaria/chamado/chamadodetail.html', {'form':form,'editor':editor,'stts':stts,'dp':dp,
                                                                   'resp':resp,'fil':fil,'array':array,
                                                                   'catg':catg})
def chamadodelete(request, tktid):
    email = get_object_or_404(EmailChamado, tkt_ref=tktid)
    if request.method == 'POST':
        ticket = TicketChamado.objects.filter(pk=email.tkt_ref_id)
        ticket.delete()
        email.delete()
        
        messages.success(request, f'Ticket {tktid} deletado com sucesso!') #HttpResponse(f'<h2>Ticket {tktid} deletado com sucesso!</h2>')
        return redirect('portaria:chamadopainel')
        
def chamado_concluido(request):
    form = TicketChamado.objects.filter(status='CONCLUIDO', dt_abertura__year=datetime.datetime.now().year,
                                        dt_abertura__month=datetime.datetime.now().month)
    if request.method == 'POST':
        date1 = datetime.datetime.strptime(request.POST.get('date1'), '%Y-%m-%d').replace(hour=00, minute=00)
        date2 = datetime.datetime.strptime(request.POST.get('date2'), '%Y-%m-%d').replace(hour=23, minute=59)
        if date1 and date2:
            form = TicketChamado.objects.filter(status='CONCLUIDO', dt_abertura__lte=date2,
                                                dt_abertura__gte=date1)
            return render(request, 'portaria/chamado/chamadosconcluidos.html', {'form': form})
    return render(request, 'portaria/chamado/chamadosconcluidos.html', {'form': form})

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
            conn = conndb()
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
                    check = EtiquetasDocumento.objects.filter(garagem=ga, tp_doc=doc, nr_doc=i['conhecimento'],
                                                         nota=i['nota_fiscal'], volume=i['volumes'])
                    if not check:
                        EtiquetasDocumento.objects.create(garagem=ga, tp_doc=doc, nr_doc=i['conhecimento'],
                                                         nota=i['nota_fiscal'], volume=i['volumes'])
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
        if code and ga != 'Selecione...':
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
        else:
            messages.error(request, 'Informações faltando, gentileza verificar')
            return redirect('portaria:bipagem_palete')
    return render(request, 'portaria/etiquetas/bipagem_palete.html', {'gachoices':gachoices})

def etqrelatorio(request):
    gachoices = TicketMonitoramento.GARAGEM_CHOICES
    return render(request, 'portaria/etiquetas/etiquetasrelatorio.html', {'gachoices':gachoices})

def romaneioxml(request):
    return render(request, 'portaria/etc/romaneioindex.html')

def painelromaneio(request):
    context = RomXML.objects.filter(pub_date__month=datetime.datetime.now().month,
                                          pub_date__year=datetime.datetime.now().year).order_by('-pub_date')
    getrem = RomXML.objects.filter(pub_date__month=datetime.datetime.now().month,
                                          pub_date__year=datetime.datetime.now().year).values_list('remetente', flat=True).distinct()
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
                print(romaneio.values())
            elif tp_dld == 'Remetente':
                romaneio = SkuRefXML.objects.filter(xmlref__id__in=romidd).annotate(
                    municipio1=F('xmlref__municipio'), uf1=F('xmlref__uf'), codigo1=F('codigo'),
                    qnt_un1=F('qnt_un'), desc_prod1=F('desc_prod'), rem=F('xmlref__remetente'),
                    romaneio_id=F('xmlref__nota_fiscal'), volume=F('xmlref__volume'), valor=F('xmlref__vlr_nf'),
                    tp_un1=F('tp_un'), peso=F('xmlref__peso'), tp_vol1=F('tp_vol'), qnt_vol1=F('qnt_vol')
                )
            elif tp_dld == 'Destinatario':
                romaneio = SkuRefXML.objects.filter(xmlref__id__in=romidd).annotate(
                    municipio1=F('xmlref__municipio'), uf1=F('xmlref__uf'), codigo1=F('codigo'),qnt_un1=F('qnt_un'),
                    desc_prod1=F('desc_prod'), dest=F('xmlref__destinatario'), romaneio_id=F('xmlref__nota_fiscal'),
                    volume=F('xmlref__volume'), valor=F('xmlref__vlr_nf'), tp_un1=F('tp_un'), peso=F('xmlref__peso'),
                    tp_vol1=F('tp_vol'), qnt_vol1=F('qnt_vol'), bairro1=F('xmlref__bairro'), cep1=F('xmlref__cep')
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
        try:
            autor = User.objects.get(id=1) if request.user not in User.objects.all() else request.user
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
                dest_bairro = mydoc.getElementsByTagName('dest')[0].getElementsByTagName('xBairro')[0].firstChild.nodeValue
                dest_cep = mydoc.getElementsByTagName('dest')[0].getElementsByTagName('CEP')[0].firstChild.nodeValue
                peso = mydoc.getElementsByTagName('transp')[0].getElementsByTagName('pesoB')[0].firstChild.nodeValue
                volume = mydoc.getElementsByTagName('transp')[0].getElementsByTagName('qVol')[0].firstChild.nodeValue
                vlr_nf = mydoc.getElementsByTagName('total')[0].getElementsByTagName('vNF')[0].firstChild.nodeValue
                skus = getText(mydoc)
                if skus:
                    try:
                        rom = RomXML.objects.create(dt_emissao=dhEmi, nota_fiscal=nf, remetente=rem, destinatario=dest,
                        peso=peso, volume=volume, vlr_nf=vlr_nf, bairro=dest_bairro, cep=dest_cep,
                                                    municipio=dest_mun, uf=dest_uf, autor=autor, xmlfile=file)
                    except Exception as e:
                        print(f'Error: {e}, error_type: {type(e).__name__}')
                        raise e
                    else:
                        for q in skus:
                            SkuRefXML.objects.create(codigo=q['sku'],desc_prod=q['descprod'],tp_un=q['un'],
                                                     qnt_un=int(q['qnt']), tp_vol=q['un2'], qnt_vol=int(q['qnt2']),
                                                     xmlref=rom)
                print('finalizado')
            else:
                pass
        except:
            continue
    return redirect('portaria:romaneioxml')

def getText(nodelist):
    doc = nodelist.getElementsByTagName('det')
    rc = []
    emit = nodelist.getElementsByTagName('emit')[0].getElementsByTagName('CNPJ')[0].firstChild.nodeValue
    for q in doc:
        var1 = q.getElementsByTagName('prod')[0]
        sku = var1.getElementsByTagName('cProd')[0].firstChild.nodeValue
        descprod = var1.getElementsByTagName('xProd')[0].firstChild.nodeValue
        un = var1.getElementsByTagName('uTrib')[0].firstChild.nodeValue
        qnt = var1.getElementsByTagName('qTrib')[0].firstChild.nodeValue.split('.')[0]
        if emit == '00763832000160':
            un2 = 'CX'
            qnt2 = q.getElementsByTagName('infAdProd')[0].firstChild.nodeValue[19:].split(' ')[0]
        else:
            un2 = var1.getElementsByTagName('uCom')[0].firstChild.nodeValue
            qnt2 = var1.getElementsByTagName('qCom')[0].firstChild.nodeValue.split('.')[0]
        all = {'sku':sku, 'descprod':descprod, 'un':un, 'qnt':qnt, 'un2':un2, 'qnt2':qnt2}
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
#romaneio para excel
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
                          'volume': q.volume, 'valor': q.valor, 'tp_un':q.tp_un1, 'peso':q.peso, 'tp_vol':q.tp_vol1,
                          'qnt_vol':q.qnt_vol1})
            if q.romaneio_id not in roms:
                roms.extend({q.romaneio_id})
        elif tp_dld == 'Destinatario':
            array.append({'municipio': q.municipio1, 'uf': q.uf1, 'codigo': q.codigo1,
                          'qnt_un': q.qnt_un1, 'desc': q.desc_prod1, 'destinatario': q.dest, 'nota': q.romaneio_id,
                          'volume': q.volume, 'valor': q.valor, 'tp_un': q.tp_un1, 'peso': q.peso, 'tp_vol':q.tp_vol1,
                          'qnt_vol':q.qnt_vol1, 'bairro':q.bairro1,'cep':q.cep1})
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
        dt = (pdr.pivot_table(index=['remetente','nota','valor','peso','desc','tp_un', 'tp_vol'],
                              values=['qnt_un', 'qnt_vol'],
                              fill_value='0')).astype(np.float)
    elif tp_dld == 'Destinatario':
        dt = (pdr.pivot_table(index=['destinatario', 'nota', 'volume', 'valor', 'peso', 'bairro', 'cep', 'desc', 'tp_un',
                                     'tp_vol'],
                              values=['qnt_un', 'qnt_vol'],
                              fill_value='0')).astype(np.float)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{datetime.datetime.today()}.xlsx"'
    writer = pd.ExcelWriter(response, engine='xlsxwriter')
    dt.to_excel(writer, 'Dinamica')
    pdr.to_excel(writer, 'Relatorio')
    writer.save()
    try:
        if response:
            return response
    except Exception as e:
        raise e
#fim das views


#funcoes variadas
@login_required
def solictransfpalete(request):
    form = TPaletesForm()
    garagem = Filiais.objects.values('sigla', 'id_garagem')
    
    if request.method == 'POST':
        ori = request.POST.get('origem_')
        des = request.POST.get('destino_')
        qnt = int(request.POST.get('quantidade_'))
        plc = request.POST.get('placa_veic')
        tp_p = request.POST.get('tp_palete')
        motorista = request.POST.get('motorista')
        conferente = request.POST.get('conferente')

        if qnt <= PaleteControl.objects.filter(loc_atual=ori,tp_palete=tp_p).count():

            currentTime = timezone.now()
            time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            solic_id = str(time).replace(':', '').replace(' ', '').replace('-', '') + plc[5:]
            if len(plc) <= 7:
                for q in range(0,qnt):
                    x = PaleteControl.objects.filter(loc_atual=ori, tp_palete=tp_p).first()
                    solic = SolicMovPalete.objects.create(solic_id=solic_id, palete=x,data_solic=currentTime,origem=ori,destino=des,
                                            placa_veic=plc,autor=request.user,motorista=motorista,conferente=conferente)
                
                    PaleteControl.objects.filter(pk=x.id).update(loc_atual="MOV")
                messages.success(request, f'{qnt} palete(s) | Aguardando o recebimento de paletes de {ori} para {des}')
                return redirect('portaria:transfdetalhe', solic_id=solic_id)
            else:
                messages.error(request,'Número de placa muito extenso.')
                return render(request,'portaria/palete/transfpaletes.html', {'form':form, 'garagem': garagem})
                
        else:
            messages.error(request,'Quantidade solicitada maior que a disponível')
            return render(request,'portaria/palete/transfpaletes.html', {'form':form, 'garagem': garagem})
    return render(request,'portaria/palete/transfpaletes.html', {'form':form, 'garagem': garagem})

def transfdetalhe(request, solic_id):
    mov = SolicMovPalete.objects.filter(solic_id=solic_id).first()
    quantity = SolicMovPalete.objects.filter(solic_id=solic_id).values('solic_id').annotate(Count("solic_id"))
    qty = quantity[0]

    data = {
        "ID Solicitação": mov.solic_id,
        "Origem": mov.origem,
        "Destino": mov.destino,
        "Placa do Veículo": upper(mov.placa_veic),
        "Data Solicitação": datetime.datetime.strftime(mov.data_solic, "%d/%m/%Y %H:%m"),
        "Quantidade": qty['solic_id__count'],
        "Autor": mov.autor.username,
        "Motorista": mov.motorista,
        "Conferente": mov.conferente
    }

    titles = ["ID Solicitação", "Origem", "Destino", "Placa Veículo", "Data Solicitação", "Quantidade", "Código de Barras", "Motorista", "Conferente"]

    #Gerar código de barras
    pdf = FPDF(orientation='P', unit='mm', format=(210, 297))
    pdf.add_page()
    pdf.ln()
    barcode = Code39(data['ID Solicitação'], writer=ImageWriter(), add_checksum=False)
    barcode.save('barcode')
    pdf.image('./barcode.png', x=48, y=150, w=120, h=30) # Posição(x, y) Tamanho(w, h)
    pdf.image('portaria/static/images/logo.png', x=160, y=10, w=35, h=17.5)
    pdf.ln()
    page_w = int(pdf.w)
    pdf.set_font("Arial", size = 20)
    pdf.cell(w=190, h=25, txt='Solicitação de transferência', border=0, align='C')
    pdf.ln(30)
    pdf.set_font("Arial", size = 12, style= 'B')

    line_height = pdf.font_size * 2.5
    for k, v in data.items():
        pdf.set_font("Arial", size = 12, style= 'B')
        pdf.cell(60, line_height, k, border=1) # com barcode = 35 e 65
        pdf.set_font("Arial", size = 12)
        pdf.cell(130, line_height, str(v), border=1, ln=1)
    pdf.output("GFG.pdf")
    with open("GFG.pdf", "rb") as f:
        response = HttpResponse(f.read(), content_type="application/pdf")
    f.close()
    os.remove("GFG.pdf")
    #os.remove("barcode.png")
    response['Content-Disposition'] = 'filename=some_file.pdf'
    return response
    #response['Content-Disposition'] = "attachment; filename='GFG.pdf'"
    #return response
    #return HttpResponse('<h2> CARALHO DE FILHO DA PUTA DE TESTE DE CORNO AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA</h2>')

def paineltransf(request):
    origem = request.GET.get('origem')
    destino = request.GET.get('destino')
    placa_veiculo = request.GET.get('placa_veiculo')
    autor = request.GET.get('autor')

    filtro = {"palete__loc_atual": "MOV"}
    if not origem is None: filtro["origem"] = origem
    if not destino is None: filtro["destino"] = destino
    if not placa_veiculo is None and placa_veiculo != "": filtro["placa_veic"] = placa_veiculo
    if not autor is None and autor != "": filtro["autor__username"] = autor

    form = SolicMovPalete.objects.filter(**filtro).values('solic_id', 'destino', 'origem', 'placa_veic', 'data_solic', 'autor__username').annotate(quantity=Count('solic_id')).order_by('data_solic')
    filiais = Filiais.objects.all()

    return render(request, 'portaria/palete/paineltransf.html', {'form': form, 'filiais': filiais})

@login_required
def transfpalete(request):
    keyga = {k:v for k,v in GARAGEM_CHOICES}
    if request.method == 'GET':
        solic_id = request.GET.get('solic_id')
        if solic_id:
            quantity = SolicMovPalete.objects.filter(solic_id=solic_id).values('solic_id').annotate(Count("solic_id"))
            for q in quantity:
                qty = q['solic_id__count']
            form = SolicMovPalete.objects.filter(solic_id=solic_id).first()
            return render(request,'portaria/palete/recpaletes.html', {"solic": form, "qty": qty})

    if request.method == 'POST':
        solic_id = request.POST.get('solic')
        dt_solic = request.POST.get('data_solic')
        qnt = int(request.POST.get('qty'))
        ori = request.POST.get('origem')
        des = request.POST.get('destino')
        plc = request.POST.get('placa_veic')
        autor = request.POST.get('autor')
        movPalete = SolicMovPalete.objects.filter(solic_id=solic_id)

        if movPalete.count() == 0:
            messages.error(request, f'Não existem mais pallets disponíveis nessa transferência')
            return redirect('portaria:painelmov')
        if int(qnt) <= int(movPalete.count()) or int(movPalete.count()) == int(qnt):
            dt_receb = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            toDelete = []
            for q in range(0, qnt):
                dt_parse = datetime.datetime.strptime(dt_solic, "%d/%m/%Y %H:%M")
                print(f'Informações do palet\niteração: {q}')
                print(f'locatual: {movPalete[q]}\n ')

                x = PaleteControl.objects.get(id=movPalete[q].palete.id)
                if x.loc_atual != des:
                    #print(x.loc_atual)
                    #print(test.loc_atual)
                    #x = PaleteControl.objects.filter(loc_atual=keyga['999'], tp_palete=movPalete[q].palete.id).first()
                    solic = MovPalete.objects.create(
                        solic_id = solic_id,
                        palete = x,
                        data_solic = datetime.datetime.strftime(dt_parse, '%Y-%m-%d %I:%M'),
                        data_receb = dt_receb,
                        origem = ori,
                        destino = des,
                        placa_veic = plc,
                        autor = request.user
                    )
                    
                    PaleteControl.objects.filter(pk=x.id).update(loc_atual=des)
                    toDelete.append(SolicMovPalete.objects.get(id=movPalete[q].id))
            for i in toDelete:
                i.delete()
            messages.success(request, 'Pallets recebidos com sucesso')
            return redirect('portaria:painelmov')
            #return render(request, 'portaria/palete/recpaletes.html')
        else:
            messages.error(request, 'A quantidade recebida é superior ao que foi enviado')
            return render(request,'portaria/palete/recpaletes.html')
    return render(request,'portaria/palete/recpaletes.html')

def painelmov(request):
    data_solic = request.GET.get('data_solic')
    data_receb = request.GET.get('data_receb')
    origem = request.GET.get('origem')
    destino = request.GET.get('destino')
    placa_veiculo = request.GET.get('placa_veiculo')
    autor = request.GET.get('autor')

    today = datetime.datetime.now().strftime('%Y-%m-%d')

    filtro = {}
    if not data_solic is None and data_solic != "": filtro["data_solic"] = data_solic
    if not data_receb is None and data_receb != "": filtro["data_receb"] = data_receb
    if not origem is None: filtro["origem"] = origem
    if not destino is None: filtro["destino"] = destino
    if not placa_veiculo is None and placa_veiculo != "": filtro["placa_veic"] = placa_veiculo
    if not autor is None and autor != "": filtro["autor__username"] = autor
    
    form = MovPalete.objects.filter(**filtro).values('solic_id', 'destino', 'origem', 'placa_veic', 'data_solic', 'data_receb', 'autor__username').annotate(quantity=Count('solic_id')).order_by('data_solic')
    filiais = Filiais.objects.all()

    return render(request, 'portaria/palete/painelmov.html', {'form': form, 'filiais': filiais, 'today': today})

@login_required
def get_nfpj_mail(request):
    a = request.POST.get('total')
    b = request.POST.get('adiantamento')
    func_id = request.POST.getlist('funcid')
    dt_1 = request.POST.get('periodo1')
    dt_2 = request.POST.get('periodo2')
    dt_pgmt = request.POST.get('dt_pgmt')
    dt_1 = datetime.datetime.strptime(dt_1 + " 00:00:00", '%Y-%m-%d %H:%M:%S')
    dt_2 = datetime.datetime.strptime(dt_2 + " 00:00:00", '%Y-%m-%d %H:%M:%S')
    dt_pgmt = datetime.datetime.strptime(dt_pgmt + " 00:00:00", '%Y-%m-%d %H:%M:%S')

    filter = {
        'id__in': func_id,
        'ativo': True
    }

    text = ""
    title = ''
    if a:
        title = 'NF'
        qs = FuncPj.objects.filter(**filter)
        text = '''Favor emitir a NF. de Prestação Serviços

    Período de: {16} à {17}

    Valor do Serviço: R$ {2:.2f}
    Premio: R$ {3:2f}
    Ajuda de custo: R$ {4:.2f}
    Crédito Convênio: R$ {5:.2f}
    Outros Créditos: R$ {6:.2f}

    Adiantamento: R$ {7:.2f}
    Desconto Convênio: R$ {8:.2f}
    Outros Descontos: R$ {9:.2f}

    Total Pagamento: R$ {10:.2f}
    Data de pagamento: {18}
    Serviço Prestado em: {0}
    Dados Bancários: 
        Banco : {12}
        Ag    : {13}
        C.c.  : {14}
    CPF/ CNPJ: {11}
    PIX: {20}

Att
                '''
    if b:
        title = 'NF ADIANTAMENTO'
        qs = FuncPj.objects.filter(**filter)
        text = """Prestação de Serviços 

    Período de: {16} até {17}
    Valor do Serviço: R$ {7:.2f}
    Data de pagamento: {18}
    Serviço Prestado em: {0}
    Dados Bancários: 
        Banco : {12}
        Ag    : {13}
        C.c.  : {14}
    CPF/ CNPJ: {11}
    PIX: {20}

Favor enviar a NF até {18}.

Att
                """
    array = []
    for q in qs:
        nf = NfServicoPj.objects.filter(funcionario_id=q.id).order_by('-id')

        if len(nf) > 0:
            query = FuncPj.objects.filter(pk=q.id).annotate(
                faculdade=Coalesce(nf[0].faculdade,Value(0.0)),
                cred_convenio=Coalesce(nf[0].cred_convenio,Value(0.0)),
                outros_cred=Coalesce(nf[0].outros_cred,Value(0.0)),
                aux_moradia=Coalesce(nf[0].aux_moradia,Value(0.0)),
                desc_convenio=Coalesce(nf[0].desc_convenio,Value(0.0)),
                outros_desc=Coalesce(nf[0].outros_desc,Value(0.0)),
                ) \
                .annotate(total=((F('salario') + F('ajuda_custo') + F('faculdade') + F('cred_convenio') + F('outros_cred') + F('aux_moradia')) - (F('adiantamento') + F('desc_convenio') + F('outros_desc'))))
        else:
            query = FuncPj.objects.filter(pk=q.id).annotate(
                faculdade=Coalesce(Sum('nfservicopj__faculdade', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
                cred_convenio=Coalesce(Sum('nfservicopj__cred_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
                outros_cred=Coalesce(Sum('nfservicopj__outros_cred', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
                aux_moradia=Coalesce(Sum('nfservicopj__aux_moradia',filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
                desc_convenio=Coalesce(Sum('nfservicopj__desc_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
                outros_desc=Coalesce(Sum('nfservicopj__outros_desc', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
                ) \
                .annotate(total=((F('salario') + F('ajuda_custo') + F('faculdade') + F('cred_convenio') + F('outros_cred') + F('aux_moradia')) - (F('adiantamento') + F('desc_convenio') + F('outros_desc'))))
        array.extend(query)

    for q in array:
        try:
            send_mail(
                subject=title,
                message=text.format(
                    f'{q.filial.nome} - {q.filial.uf}', q.nome, q.salario, q.faculdade, q.ajuda_custo + q.aux_moradia, q.cred_convenio,
                    q.outros_cred, q.adiantamento, q.desc_convenio, q.outros_desc, q.total,
                    q.cpf_cnpj, q.banco, q.ag, q.conta, q.op,
                    dt_1.strftime('%d/%m/%Y'), dt_2.strftime('%d/%m/%Y'), dt_pgmt.strftime('%d/%m/%Y'),
                    q.aux_moradia, q.pix or "Não Informado"
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[q.email, 'lucas.feitosa@bora.com.br', 'daniel.domingues@bora.com.br'],
                fail_silently=False
            )
            MailsPJ.objects.create(funcionario_id=q.id, data_pagamento=dt_pgmt,
                                   mensagem=text.format(
                    f'{q.filial.nome} - {q.filial.uf}', q.nome, q.salario, q.faculdade, q.ajuda_custo, q.cred_convenio,
                    q.outros_cred, q.adiantamento, q.desc_convenio, q.outros_desc, q.total,
                    q.cpf_cnpj, q.banco, q.ag, q.conta, q.op, dt_1, dt_2, dt_pgmt, q.aux_moradia, q.pix
                ))
        except Exception as e:
            print(e)
            messages.error(request, f"Erro ao enviar o Email do {q.nome.upper()}")
            return redirect('portaria:consultanfpj')
    
    messages.success(request, 'Emails enviado com sucesso.')
        
    return redirect('portaria:consultanfpj')

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
    
    print(date1)
    print(date2)
    # Maneira que encontrei de fazer funcionar
    #palete = MovPalete.objects.all() # Tirar da formação do CSV data_ult_mov
    # OU
    # Gerar CSV e fazer filtragem por Filial

    # Código original do Gabriel que estava os campos estão errados
    palete = MovPalete.objects.filter(data_ult_mov__lte=date2, data_ult_mov__gte=date1)

    # Funciona mas não tem o campo de filtragem
    #palete = MovPalete.objects.filter(data_solic=date2, data_receb=date1) # Para funcionar colocar data_receb e data_solic - data_ult_mov | data_ult_mov__gte
    
    if palete:
        print('Entrou no IF')
        for q in palete:
            array.append({'origem':q.origem, 'destino':q.destino, 'data_ult_mov':q.data_ult_mov, 'placa':q.placa_veic,
                          'autor':q.autor, 'tipo': q.palete.tp_palete if q.palete else 'DEVOLVIDO'})
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
        messages.error(request,'Por favor, digite uma data válida')
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
            # recipient_list=[func.email]
            recipient_list=["davi.bezerra@bora.com.br"]
        )

    except ValueError:
        messages.error(request, 'Erro')
        return redirect('portaria:feriasview')
    else:
        messages.success(request, f'Email enviado para {func}')
        return redirect('portaria:feriasview')


def get_nfpj_csv(request):
    array = []
    ini = None
    fim = None

    if request.POST.get('dataini'):
        ini = datetime.datetime.strptime(request.POST.get('dataini'), '%Y-%m-%d').date()
    if request.POST.get('datafim'):
        fim = datetime.datetime.strptime(request.POST.get('datafim'), '%Y-%m-%d').date()

    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition':'attatchment; filename="servicospj.csv"'})
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(['nome','cpf/cnpj', 'data emissao','salario','ajuda de custo','adiantamento','credito convenio','outros creditos',
                     'desconto convenio','outros descontos','total a pagar'])
    
    order_by = "nome"
    filter = {'ativo': 1}

    if ini:
        filter['nfservicopj__data_emissao__gte'] = ini
    if fim:
        filter['nfservicopj__data_emissao__lte'] = fim

    qnt_funcs = FuncPj.objects.filter(**filter).order_by(order_by).distinct()

    for q in qnt_funcs:
        nfs = NfServicoPj.objects.filter(funcionario_id=q.id)

        if len(nfs) > 0:
            for nf in nfs:
                query = FuncPj.objects.filter(pk=q.id, nfservicopj=nf).annotate(
                    faculdade=Coalesce(nf.faculdade, Value(0.0)),
                    cred_convenio=Coalesce(nf.cred_convenio, Value(0.0)),
                    outros_cred=Coalesce(nf.outros_cred, Value(0.0)),
                    desc_convenio=Coalesce(nf.desc_convenio, Value(0.0)),
                    outros_desc=Coalesce(nf.outros_desc, Value(0.0)),
                    data_emissao=Coalesce('nfservicopj__data_emissao', datetime.date.today())
                ).annotate(total=((F('salario') + F('ajuda_custo') + F('faculdade') + F('cred_convenio') + F('outros_cred')) - (F('adiantamento') + F('desc_convenio') + F('outros_desc'))))
                array.extend(query)
        else:
            query = FuncPj.objects.filter(pk=q.id) \
                .annotate(
                    faculdade=Coalesce(Sum('nfservicopj__faculdade', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)),Value(0.0)),
                    cred_convenio=Coalesce(Sum('nfservicopj__cred_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
                    outros_cred=Coalesce(Sum('nfservicopj__outros_cred', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
                    desc_convenio=Coalesce(Sum('nfservicopj__desc_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
                    outros_desc=Coalesce(Sum('nfservicopj__outros_desc', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month,nfservicopj__data_emissao__year=datetime.datetime.now().year)), Value(0.0)),
                    data_emissao=Coalesce('nfservicopj__data_emissao', datetime.date.today())
                ).annotate(total=((F('salario') + F('ajuda_custo') + F('faculdade') + F('cred_convenio') + F('outros_cred')) - (F('adiantamento') + F('desc_convenio') + F('outros_desc'))))
            array.extend(query)

    for q in array:
        writer.writerow([q.nome,q.cpf_cnpj,q.data_emissao, q.salario,q.faculdade,q.cred_convenio,q.outros_cred,q.outros_cred,q.desc_convenio,q.outros_desc,q.total])

    return response

def get_checklist_csv(request):
    array = []
    try:
        ini = datetime.datetime.strptime(request.POST.get('dataini'), '%Y-%m-%d').date()
        fim = datetime.datetime.strptime(request.POST.get('datafim'), '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Por favor, digite uma data válida')
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
        messages.error(request, 'Por favor, digite uma data válida')
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
    
def get_bonus_csv(request):
    hoje = datetime.date.today()
    try:
        ini = datetime.datetime.strptime(request.POST.get('dataini'), '%Y-%m-%d').date()
        fim = datetime.datetime.strptime(request.POST.get('datafim'), '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Por favor, digite uma data válida')
        return redirect('portaria:bonuspj')
    else:
        response = HttpResponse(content_type='text/csv',
                                headers={'Content-Disposition':f'attatchment; filename=bonus/{hoje.strftime("%d/%m")}.csv"'})
        response.write(u'\ufeff'.encode('utf8'))
        writer = csv.writer(response)
        writer.writerow([
            "id","funcionario","valor_pagamento","data_pagamento",
            "observacao","quitado","data_quitacao","data_criacao", "autor"
        ])

        bonus = BonusPJ.objects.all().values_list(
            "id","funcionario","valor_pagamento","data_pagamento",
            "observacao","quitado","data_quitacao","data_criacao", "autor"
        ).filter(data_pagamento__gte=ini,data_pagamento__lte=fim)

        for linha in bonus:
            writer.writerow(linha)

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
    #send = ['IGOR.ROSARIO@BORA.COM.BR','ROBERT.DIAS@BORA.COM.BR', request.user.email] + orig.cc.split(',') + mailfil.split(',')
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
            sm.sendmail(get_secret('EUSER_MN'), orig.cc.split(';'), msg1.as_string())#############
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
    msg1['From'] = get_secret('EUSER_MN') ################### alterar
    msg1['To'] = dict["solic"] ################### alterar
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

def chamadoupdate(request,tktid,area, myfile):
    media = ''
    attatch = ''
    hoje = datetime.date.today()
    rr = random.random()
    path = settings.STATIC_ROOT + '/chamados/' + str(hoje) + '/'
    pattern = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp)')
    pattern2 = re.compile(r'/static/chamados/\S+(?i:jpeg|jpg|gif|png|bmp)')
    orig = get_object_or_404(EmailChamado, tkt_ref_id=tktid)
    try:
        if orig.tkt_ref.servico == 'PRAXIO':
            user = 'chamado.praxio@bora.tec.br'
        elif orig.tkt_ref.servico == 'DESCARGA':
            user = 'chamado.descarga@bora.tec.br'
        elif orig.tkt_ref.servico == 'JURIDICO':
            user = 'chamado.juridico@bora.tec.br'
        elif orig.tkt_ref.servico == 'COMPROVANTE':
            user = 'chamado.comprovantes@bora.tec.br'
        elif orig.tkt_ref.servico == 'FISCAL':
            user = 'chamado.fiscal@bora.tec.br'
        elif orig.tkt_ref.servico == 'MANUTENCAO':
            user = 'chamado.manutencao@bora.tec.br'
        elif orig.tkt_ref.servico == 'ALMOXARIFADOS':
            user = 'chamado.almoxarifado@bora.tec.br'
        if request.method == 'POST':
            msg1 = MIMEMultipart()
            msg = area
            msg2 = area
            if myfile is not None:
                for q in myfile:
                    locimg = os.path.join(path, str(q))
                    if os.path.exists(os.path.join(path)):
                        fp = open(locimg, 'wb')
                        fp.write(q.read())
                        fp.close()
                        os.chmod(locimg, 0o777)
                        try:
                            os.rename(locimg, os.path.join(path, str(rr) + str(q)))
                        except:
                            os.rename(locimg, os.path.join(path, str(rr) + str(q) + str(random.randint(1,100))))
                    else:
                        os.mkdir(path=path)
                        os.chmod(path, 0o777)
                        fp = open(locimg, 'wb')
                        fp.write(q.read())
                        fp.close()
                        os.chmod(locimg, 0o777)
                        try:
                            os.rename(locimg, os.path.join(path, (str(rr) + str(q))))
                        except:
                            os.rename(locimg, os.path.join(path, str(rr) + str(q) + str(random.randint(1,100))))
                    item = os.path.join('/static/chamados/' + str(hoje) + '/', (str(rr) + str(q)))
                    aatt = '<div class="mailattatch"><a href="' + item + '" download><img src="/static/images/downicon.png" width="40"><p>' + str(
                        q) + '</p></a></div>'
                    attatch += aatt
                    q.seek(0)
                    part = MIMEApplication(q.read(), name=str(q))
                    part['Content-Disposition'] = 'attachment; filename="%s"' % q
                    msg1.attach(part)

            if re.findall(pattern, msg):
                for q in re.findall(pattern,msg):
                    media = q
                    img_data = open(('/home/bora/www' + media), 'rb').read()
                    msgimg = MIMEImage(img_data, name=os.path.basename(media), _subtype='jpg')
                    msgimg.add_header('Content-ID', f'{media}')
                    msg1.attach(msgimg)
                    msg = msg.replace(('src="' + media + '"'), f'src="cid:{media}" ')
            if orig.ult_resp:
                nmsg = '<div class="container chmdimg">' + msg + '</div>' + orig.ult_resp.split('<p>Anterior</p><hr>')[0]
                nmsg2 = '<div class="container chmdimg">' + msg2 + '</div>' + orig.ult_resp_html.split('<p>Anterior</p><hr>')[0]
            else:
                nmsg = '<div class="container chmdimg">' + msg + '</div>' + orig.mensagem.split('<div class="mailattatch">')[0]
                nmsg2 = '<div class="container chmdimg">' + msg2 + '</div>' + orig.mensagem.split('<div class="mailattatch">')[0]
            if re.findall(pattern2, nmsg):
                array = []
                for q in re.findall(pattern2, nmsg):
                    fp = open(('/home/bora/www' + q), 'rb')
                    img_data = fp.read()
                    msgimg2 = MIMEImage(img_data, name=os.path.basename(q), _subtype='jpg')
                    msgimg2.add_header('Content-ID', f'{os.path.basename(q)}')
                    for i in msgimg2.walk():
                        if i['Content-ID'] not in array:
                            msg1.attach(msgimg2)
                            nmsg = nmsg.replace((f'="{q}"'), f'="cid:{os.path.basename(q)}"')
                            array.append(i['Content-ID'])
            nmsg2 = nmsg2.replace(f'<p>Anterior</p><hr>', '<hr>')
            nmsg = nmsg.replace(f'<p>Anterior</p><hr>', '<hr>')
            if orig.ult_resp is not None:
                aa = nmsg + orig.ult_resp
                bb = '<hr>' + str(request.user) + ' -- ' + str(dateformat.format(timezone.now(), 'd-m-Y H:i')) + '<br>' + nmsg2 + '<br>' + attatch + '<p>Anterior</p><hr>' + orig.ult_resp_html
            else:
                aa = nmsg
                bb = '<hr>' + str(request.user) + ' -- ' + str(dateformat.format(timezone.now(), 'd-m-Y H:i')) + '<br>' + nmsg2 + '<br>' + attatch
            send = orig.tkt_ref.solicitante + ','
            send += orig.cc if orig.cc else send.replace(',', '')
            msg1['Subject'] = orig.assunto
            msg1['In-Reply-To'] = orig.email_id
            msg1['References'] = orig.email_id
            msg_id = make_msgid(idstring=None, domain='bora.com.br')
            msg1['Message-ID'] = msg_id
            msg1['From'] = user
            msg1['To'] = orig.tkt_ref.solicitante
            msg1['Cc'] = orig.cc
            msg1.attach(MIMEText(nmsg, 'html', 'utf-8'))
            smtp_h = 'smtp.bora.com.br'
            smtp_p = '587'
            passw = 'B0r*610580'
            #passw = 'Bor@456987'
            try:
                sm = smtplib.SMTP('smtp.bora.tec.br', '587')
                sm.set_debuglevel(1)
                sm.login(user, 'Bor4@123')
                print('Logado com sucesso')
                sm.sendmail(user, send.split(','), msg1.as_string())
                EmailChamado.objects.filter(pk=orig.id).update(ult_resp=aa, ult_resp_html=bb,ult_resp_dt=dateformat.format(timezone.now(),'Y-m-d H:i'))
            except Exception as e:
                print(f'ErrorType:{type(e).__name__}, Error:{e}')
            else:
                messages.success(request, 'Resposta enviada com sucesso!')
        else:
            print('nao entrou no if')
    except:
        raise

def chamadoreadmail(request):
    #params
    tkt = None
    service = ''
    hoje = datetime.date.today()
    host = 'pop.kinghost.net'
    mails = ['chamado.praxio2@bora.tec.br']
    for e_user in mails:
        e_pass = 'Bor4@123' #'Bor@456987'
        pattern1 = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp)')
        pattern2 = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp).\w+.\w+')

        # POP descontinuado - Mudança para OAUTH2(imaplib) necessária
        #logando no email
        
        pp = poplib.POP3(host)
        pp.set_debuglevel(1)
        print(e_user, e_pass)
        pp.user(e_user)
        pp.pass_(e_pass)      
        print('Logado com sucesso')

        #pp = imaplib.IMAP4_SSL(host)

        num_messages = len(pp.list()[1]) #conta quantos emails existem na caixa

        for i in range(num_messages):
	    
            rr = random.random()
            attatch = ''
            e_cc_a = ''
            try:
                print('parsing email...')
                raw_email = b'\n'.join(pp.retr(i+1)[1]) #pega email
                parsed_email = email.message_from_bytes(raw_email, policy=policy.compat32)
                #print('email parsed...')
            except Exception as e:
                print(f'Error type:{type(e).__name__}, error: {e}')
            else:
                #print('email is multipart?', parsed_email.is_multipart())
                if parsed_email.is_multipart():
                    #caminha pelas partes do email e armazena dados e arquivos
                    for part in parsed_email.walk():
                        # funcao para pegar codificacao
                        cs = parsed_email.get_charsets()
                        for q in cs:
                            if q is None:
                                continue
                            else:
                                cs = q
                        ctype = part.get_content_type()
                        cdispo = str(part.get('Content-Type'))
                        if ctype == 'text/plain' and 'attatchment' not in cdispo:
                            body = part.get_payload(decode=True)
                            htbody = body
                        elif ctype == 'text/html' and 'attatchment' not in cdispo:
                            body = part.get_payload(decode=True)
                        if ctype == 'text/html' and 'attatchment' not in cdispo:
                            htbody = part.get_payload(decode=True)
                        filename = part.get_filename()
                        #print('if have filename...')
                        if filename:
                            #print('have filename')
                            filename = decode_header(filename)
                            #print('filename: ', filename)
                            try:
                                filename = filename[0][0].decode(cs)
                            except:
                                filename = filename[0][0]
                            path = settings.STATIC_ROOT + '/chamados/' + str(hoje) + '/'
                            #print('path: ', path)
                            locimg = os.path.join(path, filename)
                            #print('locimg complete...')
                            if os.path.exists(os.path.join(path)):
                                # print('os.path exists')
                                fp = open(locimg, 'wb')
                                fp.write(part.get_payload(decode=True))
                                fp.close()
                                os.chmod(locimg, 0o777)
                                try:
                                    os.rename(locimg, os.path.join(path, (str(rr) + filename)))
                                except Exception as e:
                                    os.rename(locimg, os.path.join(path, (str(rr) + filename + str(random.randint(1,100)))))
                            else:
                                try:
                                    os.mkdir(path)
                                    #print('creating directory...')
                                    os.chmod(path, 0o777)
                                    #print('give permission...')
                                    fp = open(locimg, 'wb')
                                    fp.write(part.get_payload(decode=True))
                                    fp.close()
                                    os.chmod(locimg, 0o777)
                                    
                                except Exception as e:
                                    print('error on creating erro:', e)
                                try:
                                    os.rename(locimg, os.path.join(path, (str(rr) + filename)))
                                except Exception as e:
                                    os.rename(locimg, os.path.join(path, (str(rr) + filename + str(random.randint(1,100)))))
                            item = os.path.join(('/static/chamados/' + str(hoje) + '/'), (str(rr) + filename))
                            aa = '<div class="mailattatch"><a href="'+item+'" download><img src="/static/images/downicon.png" width="40"><p>'+filename[:-4]+'</p></a></div>'
                            attatch += aa
                else:
                    
                    body = parsed_email.get_payload(decode=True)
                    htbody = body
                    cs = parsed_email.get_charsets()
                    for q in cs:
                        if q is None:
                            continue
                        else:
                            cs = q
                
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
                if e_to:
                    e_to = e_to.lower()
                    for q in re.findall(r'<(.*?)>', e_to):
                        if q not in ['chamado.praxio@bora.tec.br', 'chamado.juridico@bora.tec.br','chamado.descarga@bora.tec.br', 'chamado.comprovantes@bora.tec.br', 
                                     'chamado.fiscal@bora.tec.br','chamado.manutencao@bora.tec.br', 'chamado.almoxarifado@bora.tec.br']:
                            e_cc_a += q + ','
                e_cc = parsed_email['CC']
                if e_cc:
                    e_cc = e_cc.lower()
                    for q in re.findall(r'<(.*?)>', e_cc):
                        if q not in ['chamado.praxio@bora.tec.br', 'chamado.juridico@bora.tec.br','chamado.descarga@bora.tec.br', 'chamado.comprovantes@bora.tec.br', 
                                     'chamado.fiscal@bora.tec.br','chamado.manutencao@bora.tec.br', 'chamado.almoxarifado@bora.tec.br']:
                            e_cc_a += q + ','
                get_serv = (str(parsed_email['Cc']) +' '+ str(parsed_email['To'])).lower()
                if 'chamado.praxio@bora.tec.br' in get_serv:
                    service = 'PRAXIO'
                if 'chamado.descarga@bora.tec.br' in get_serv:
                    service = 'DESCARGA'
                if 'chamado.comprovantes@bora.tec.br' in get_serv:
                    service = 'COMPROVANTE'
                if 'chamado.fiscal@bora.tec.br' in get_serv:
                    service = 'FISCAL'
                if 'chamado.juridico@bora.tec.br' in get_serv:
                    service = 'JURIDICO'
                if 'chamado.manutencao@bora.tec.br' in get_serv:
                    service = 'MANUTENCAO'
                if 'chamado.almoxarifado@bora.tec.br' in get_serv:
                    service = 'ALMOXARIFADOS'
                if 'chamado.compras@bora.tec.br' in get_serv:
                    service = 'COMPRAS'
                print(service)
                e_id = parsed_email['Message-ID'].strip()
                e_ref = parsed_email['References']
                if e_ref is None: e_ref = e_id
                else: e_ref = e_ref
                e_irt = parsed_email['In-Reply-To']
                try:
                    inreply = e_ref.strip() + ' ' + e_irt.strip()
                    inreply = inreply.replace('\n',' ').replace(' ', ',').split(',')
                except Exception as e:
                    inreply = e_ref.strip()
                #separa conteudo email, e pega attatchments
                e_body = body.decode(cs)
                w_body = '<div class="container chmdimg">' + htbody.decode(cs) + '</div>'
                print('stating find pattern')
                if re.findall(pattern2, w_body):
                    for q in re.findall(pattern2, w_body):
                        new = re.findall(pattern1, q)
                        if re.findall(f'/media/django-summernote/{str(hoje)}/', q):
                            new_cid = os.path.join(settings.STATIC_URL + 'chamados/' + str(hoje) + '/', (str(rr) +
                                                    new[0].split(f'cid:/media/django-summernote/{str(hoje)}/')[1]))
                        else:
                            try:
                                new_cid = os.path.join(settings.STATIC_URL + 'chamados/' + str(hoje) + '/',
                                                   (str(rr) + new[0].split('cid:')[1]))
                            except Exception as e:
                                new_cid = os.path.join(settings.STATIC_URL + 'chamados/' + str(hoje) + '/',
                                                       (str(rr) + q))

                        w_body = w_body.replace(q, new_cid)
                        e_body = e_body.replace(q, new_cid)
                elif re.findall(pattern1, w_body):
                    for q in re.findall(pattern1, w_body):
                        new = re.findall(pattern1, q)
                        try:
                            if re.findall(f'/media/django-summernote/{str(hoje)}/', q):
                                new_cid = os.path.join(settings.STATIC_URL + 'chamados/' + str(hoje) + '/', (str(rr) +
                                                       new[0].split(f'cid:/media/django-summernote/{str(hoje)}/')[1]))
                            else:
                                try:
                                    new_cid = os.path.join(settings.STATIC_URL + 'chamados/' + str(hoje)
                                                       + '/', (str(rr) + new[0].split('cid:')[1]))
                                except Exception as e:
                                    new_cid = os.path.join(settings.STATIC_URL + 'chamados/' + str(hoje) + '/',
                                                           (str(rr) + new[0].split('cid:')[1]))
                        except Exception as e:
                            print(f'ErrorType: {type(e).__name__}, Error: {e}')
                        else:
                            w_body = w_body.replace(q, new_cid)
                            e_body = e_body.replace(q, new_cid)
                print('creating ticket')
                try:
                    form = EmailChamado.objects.filter(email_id=inreply[0])
                except Exception as e:
                    print(e)
                else:
                    if form.exists():
                        print('form exists')
                        try:
                            tkt = TicketChamado.objects.get(pk=form[0].tkt_ref_id)
                            print(tkt.msg_id, tkt.nome_tkt)
                        except Exception as e:
                            print(f'Error:{e}, error_type:{type(e).__name__}')
                        else:
                            print('updating chamado')
                            if form[0].ult_resp is not None:
                                aa = '<hr>' + e_body + '<p>Anterior</p><hr>' + form[0].ult_resp
                                bb = '<hr>' + e_from + ' -- ' + e_date + '<br>' + w_body + '<br>' + attatch + '<p>Anterior</p><hr>' + form[0].ult_resp_html
                            else:
                                aa = '<hr>' + e_body
                                bb = '<hr>' + e_from + ' -- ' + e_date + '<br>' + w_body + '<br>' + attatch
                            form.update(ult_resp=aa, ult_resp_html=bb, ult_resp_dt=e_date)
                    else:
                        try:
                            print('form dont exist')
                            newtkt = TicketChamado.objects.create(solicitante=e_from, servico=service, nome_tkt=e_title,
                                                                  dt_abertura=e_date, status='ABERTO', msg_id=e_id)
                            mensagem = '<hr>' + e_from + ' -- ' + e_date + w_body + attatch
                            newmail = EmailChamado.objects.create(assunto=e_title, mensagem=mensagem, cc=e_cc_a, dt_envio=e_date,
                                                                  email_id=e_id, tkt_ref=newtkt)
                        except Exception as e:
                            print('error: ', e, 'type: ', type(e).__name__)
            pp.dele(i + 1)
        pp.quit()
    return HttpResponse('<h2>Job done!</h2>')

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
    columns = [col[0].lower() for col in cursor.description]
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
    sm = smtplib.SMTP('smtp.bora.tec.br', '587')
    sm.set_debuglevel(1)
    sm.login(get_secret('KH_MDFUSER'), get_secret('KH_MDFPASS'))
    hoje = datetime.date.today()
    gachoices = GARAGEM_CHOICES
    mailchoices = {
                    'SPO': [''],
                    'MG':  [''],
                    'TMA': [''],
                    'BMA': [''],
                    'BPE': [''],
                    'BPB': [''],
                    'BAL': [''],
                    'TCO': ['juliano.oliveira@borexpress.com.br', 'lino.loureiro@borexpress.com.br',
                            'rogeria.loureiro@borexpress.com.br'],
                    'GVR': ['mauricio@bora.com.br'],
                    'VIX': ['renata.cesario@bora.com.br'], 		
                    'UDI': ['marcus.silva@borexpress.com.br', 'tulio.pereira@borexpress.com.br'],
                    'CTG': ['ygor.henrique@borexpress.com.br','samuel.santos@borexpress.com.br','junior.morais@borexpress.com.br'],
                    'MCZ': ['rafael@bora.com.br', 'carlos.eduardo@bora.com.br','ronnielly@bora.com.br'],
                    'SSA': ['jaqueline.santos@bora.com.br', 'brandao.alan@bora.com.br'],
                    'NAT': ['ronnielly@bora.com.br', 'lindalva@bora.com.br', 'lidianne@bora.com.br'],
                    'SLZ': ['felipe@bora.com.br'],
                    'THE': ['felipe@bora.com.br'],
                    'BEL': ['felipe@bora.com.br'],
                    'VDC': ['jose.sousa@bora.com.br', 'fernando.sousa@bora.com.br', 'brandao.alan@bora.com.br'],
                    'REC': ['cinthya.souza@bora.com.br', 'patricia.santos@bora.com.br', 'edvanio.silva@bora.com.br',
                            'expedicao_rec@bora.com.br','ronnielly@bora.com.br'],
                    'AJU': ['luana.santos@bora.com.br','brandao.alan@bora.com.br'],
                    'JPA': ['patricia.lima@bora.com.br','ronnielly@bora.com.br'],
                    'FOR': ['luciano@bora.com.br', 'aldeci.oliveira@bora.com.br','ronnielly@bora.com.br']
                   }
    for k, v in gachoices:
        result = mailchoices.get(v, '')
        conn = conndb()
        cur = conn.cursor()
        cur.execute(f"""
                    SELECT DISTINCT
                           E5.CODIGO MDFE,
                           E5.DATA_SAIDA SAIDA_VEIC,
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
                           E5.TIPO_DOCTO = 58                               AND
                           
                           E5.ID_GARAGEM = {k}                              AND
                           E5.ID_GARAGEM <> 1                               AND
                           BG.STATUS = 'A'                                  AND
                           
                           BG.DATA_ENVIO BETWEEN ((SYSDATE)-1) AND (SYSDATE)
                    """)
        res = dictfetchall(cur)
        cur.close()
        pdr = pd.DataFrame(res)
        if not pdr.empty:
            send = ['gabriel.torres@bora.com.br', 'alan@bora.com.br', 'gabriel.moura@bora.com.br',
                    'thiago@bora.com.br', 'rafael.rocha@bora.com.br'] 
            for i in result:
                send.append(i)
            print(send)
            #send = ['gabriel.torres@bora.com.br']
            #Separa congelado inicio
            if k in ('6','7'):
                resultrec = mailchoices.get('REC', '')
                try:
                    row = pdr.loc[pdr['descricao_prod'] == 'CONGELADO']
                except Exception as e:
                    print(f'Error:{e}, error_type:{type(e).__name__}')
                else:
                    pdr = pdr.drop(row.index)
                    if not row.empty:
                        send2 = ['gabriel.torres@bora.com.br', 'alan@bora.com.br', 'gabriel.moura@bora.com.br',
                                 'thiago@bora.com.br', 'rafael.rocha@bora.com.br']
                        for i in result:
                            send2.append(i)
                        print(send2)
                        #send2 = ['gabriel.torres@bora.com.br', 'alan@bora.com.br']
                        msg = MIMEMultipart('related')
                        msg['From'] = get_secret('KH_MDFUSER')
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
                        print(row)
                        row['saida_veic'] = pd.to_datetime(row['saida_veic'], format='%d/%m/%Y').dt.strftime('%d/%m/%Y')
                        row['leadtime'] = pd.to_datetime(row['leatime'], format='%d/%m/%Y').dt.strftime('%d/%m/%Y')
                        row.to_excel(buffer, engine='xlsxwriter', index=False)
                        part = MIMEApplication(buffer.getvalue(), name=v)
                        part['Content-Disposition'] = 'attachment; filename=%s.xlsx' % v

                        msg.attach(part)
                        try:
                            #sm.sendmail(get_secret('EUSER_MN'), send2, msg.as_string())
                            sm.sendmail(get_secret('KH_MDFUSER'), send2, msg.as_string())
                        except Exception as e:
                            raise e
                        # Separa congelado fim

            msg = MIMEMultipart('related')
            msg['From'] = get_secret('KH_MDFUSER')
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
            pdr['saida_veic'] = pd.to_datetime(pdr['saida_veic'], format='%d/%m/%Y').dt.strftime('%d/%m/%Y')
            pdr['leadtime'] = pd.to_datetime(pdr['leadtime'], format='%d/%m/%Y').dt.strftime('%d/%m/%Y')
            pdr.to_excel(buffer, engine='xlsxwriter', index=False)
            part = MIMEApplication(buffer.getvalue(), name=v)
            part['Content-Disposition'] = 'attachment; filename=%s.xlsx' % v

            msg.attach(part)
            try:
                sm.sendmail(get_secret('KH_MDFUSER'), send, msg.as_string())
            except Exception as e:
                return HttpResponse(f'<h3> Falha no envio do email {k} para {send},</h3><p>conteúdo: {msg.as_string()}</p><br><h3>Erro: {e} <br> Tipo: {type(e)}</h3>')
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
                                  'data_bipagem':q.bip_date, 'volume':q.volume_conf, 'nf':q.etq_ref.nota_fiscal,
                                  'localizacao':q.etq_ref.localizacao, 'autor':q.autor.username})
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
    filiais = Filiais.objects.all()
    justchoices = JustificativaEntrega.JUSTIFICATIVA_CHOICES
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(1)
    today = today.strftime('%Y-%m-%d')
    yesterday = yesterday.strftime('%Y-%m-%d')
    
    if request.method == 'GET':
        date1 = request.GET.get('data1')
        date2 = request.GET.get('data2')
        garagem = request.GET.get('garagem')
        if date1 and date2 and garagem:
            form = JustificativaEntrega.objects.filter(
                    filial__id_garagem=garagem, data_emissao__lte=date2, data_emissao__gte=date1,
                    confirmado=False
                ).order_by(
                    "lead_time"
                )
            
            form_serialized = JustificativaEntregaSerializer(form, many=True).data
            justificativa = JustificativaEntrega.objects.get(id=14560)
            serializer = JustificativaEntregaSerializer(justificativa)
            # print(serializer.data)
            
            # ipdb.set_trace()
                                                        
            return render(request,'portaria/etc/justificativa.html', 
                            {
                                'form':form_serialized,
                                'filiais':filiais,
                                'justchoices':justchoices,
                                'today': today, 
                                'yesterday': yesterday
                            }
                        )

    if request.method == 'POST':
        lista = request.POST.getlist('counter')
        for q in lista:
            if request.POST.get(f'ocor{q}') is not None:
                idocor = request.POST.get(f'ocor{q}')
                idobj = request.POST.get(f'idobj{q}')
                result = dict(justchoices).get(request.POST.get(f'ocor{q}'))
                try:
                    obj = get_object_or_404(JustificativaEntrega, pk=idobj)
                except Exception as e:
                    print(f'Error:{e}, error_type:{type(e).__name__}')
                else:
                    obj.cod_just = idocor
                    obj.desc_just = result
                    obj.autor = request.user
                    if request.FILES.get(f'file{q}'):
                        file = request.FILES.get(f'file{q}')
                        obj.file = file
                    obj.save()
        messages.success(request, 'Justificativas cadastradas')
        return redirect('portaria:justificativa')
    return render(request, 'portaria/etc/justificativa.html', {'filiais': filiais, 'today': today, 'yesterday': yesterday})

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

def confirmjust(request):
    gachoices = FILIAL_CHOICES
    form = JustificativaEntrega.objects.filter(cod_just__isnull=False, desc_just__isnull=False, confirmado=False)
    if request.method == 'GET':
        date1 = request.GET.get('data1')
        date2 = request.GET.get('data2')
        filial = request.GET.get('filial')
        if date1 and date2 and filial:
            form = JustificativaEntrega.objects.filter(id_garagem=filial, data_emissao__lte=date2,
                                                       data_emissao__gte=date1, confirmado=False,
                                                       cod_just__isnull=False, desc_just__isnull=False)
            return render(request, 'portaria/etc/confirmjustificativas.html', {'form': form, 'gachoices': gachoices})
    if request.method == 'POST':
        aa = request.POST.getlist('romid')
        for q in aa:
            try:
                if 'false' in q:
                    sts = q.split('-')[1]
                    q = q.split('-')[0]
                else:
                    q = q
                    sts = None
                obj = get_object_or_404(JustificativaEntrega, pk=q)
            except Exception as err:
                print(err)
                continue
            else:
                if sts:
                    obj.recusa = True
                else:
                    obj.confirmado = True
                obj.save()
    return render(request, 'portaria/etc/confirmjustificativas.html', {'form':form,'gachoices':gachoices})
    
def pivot_rel_just(date1, date2):
    array = []
    gachoices = GARAGEM_CHOICES
    dictga = {k:v for k,v in gachoices}
    compare_date = datetime.datetime.strptime('0001-01-01', '%Y-%m-%d')
    if date1 and date2:
        qs = JustificativaEntrega.objects.filter(data_emissao__lte=date2, data_emissao__gte=date1)
    else:
        qs = JustificativaEntrega.objects.all()

    for q in qs:
        
        # O erro está no campo ID_Garagem
        # Verificar se o correto é (dictga:q.id_garagem ou q.id_garagem)

        array.append({'ID_GARAGEM':q.id_garagem,'CONHECIMENTO':q.conhecimento, 'TIPO_DOC': q.tipo_doc,
                      'DATA_EMISSAO':q.data_emissao,'REMETENTE':q.remetente,'DESTINATARIO':q.destinatario,
                      'PESO':q.peso, 'LEAD_TIME':q.lead_time,'EM_ABERTO':q.em_aberto,'LOCAL_ENTREGA':q.local_entreg,
                      'NOTA_FISCAL':q.nota_fiscal,'COD_JUST':q.cod_just,'DESC_JUST':q.desc_just,
                      'AUTOR':q.autor,
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
    host = get_secret('EHOST_XML')
    user = get_secret('ESEND_XML')
    pasw = get_secret('EPASS_XML')
    pp = poplib.POP3(host)
    pp.set_debuglevel(1)
    pp.user(user)
    pp.pass_(pasw)
    xmlsarray = []
    num_messages = len(pp.list()[1])
    for i in range(num_messages):
        print('for num_messages')
        raw_email = b'\n'.join(pp.retr(i+1)[1])
        parsed_mail = email.message_from_bytes(raw_email)
        if parsed_mail.is_multipart():
            print('email is multipart')
            for part in parsed_mail.walk():
                print('for part in parsed_email')
                filename = part.get_filename()
                if re.findall(re.compile(r'\w+(?i:.xml|.XML)'), str(filename)):
                    print('find xml')
                    xmlsarray.extend({part.get_payload(decode=True)})
        pp.dele(i+1)
    pp.quit()
    try:
        print(xmlsarray)
        await entradaxml(request, args=xmlsarray)
    except Exception as e:
        print(f'Error: {e}, error_type: {type(e).__name__}')
        return HttpResponse(f'<h2> Ocorreu um erro durante a consulta - XML </h2> <br> Erro: {e} <br> Tipo do erro: {type(e).__name__}')
        pass
    return HttpResponse('<h2>Consulta finalizada!</h2>')

def compras_index(request):
    filchoices = FILIAL_CHOICES
    item_solicitante = SolicitacoesCompras.objects.exclude(Q(status='CONCLUIDO') | Q(status='CANCELADO'))\
        .filter(data__month=datetime.datetime.now().month,data__year=datetime.datetime.now().year).values('responsavel__username')\
        .annotate(total=Count('responsavel'))
    metrics = SolicitacoesCompras.objects.annotate(
        concl=Count('id', filter=Q(status='CONCLUIDO')),
        andam=Count('id',filter=(Q(status='ANDAMENTO') | Q(status='APROVADO') | Q(status='ABERTO'))),
        ).aggregate(concluido=Sum('concl'), andamento=Sum('andam'))
    return render(request, 'portaria/etc/compras.html', {'filchoices':filchoices,'item_solicitante':item_solicitante,
                                                         'metrics':metrics})

def compras_lancar_pedido(request):
        # print('lançando pedido...')
        # idsolic = request.POST.get('getid')
        # empresa = request.POST.get('empresa')
        # fil = request.POST.get('filial')
        # anexo = request.FILES.get('getanexo')
        # if idsolic:
        #     print(f'gakey: {gakey[empresa+fil]}')
        #     print('stating db conmection...')
        #     conn = conndb()
        #     cur = conn.cursor()
        #     print('execute db select')
        #     try:
        #         cur.execute(f"""
        #                     SELECT 
        #                            SO.NUMEROSOLIC NR_SOLICITACAO,
        #                            CM.DESCRICAOMAT PRODUTO,
        #                            SO.DATASOLIC DATA,
        #                            CIS.QTDEITSOLIC QTD_ITENS,
        #                            CASE
        #                                WHEN SO.STATUSSOLIC = 'A' THEN 'ABERTO'
        #                                WHEN SO.STATUSSOLIC = 'P' THEN 'APROVADO'
        #                                WHEN SO.STATUSSOLIC = 'F' THEN 'FECHADO'
        #                            END STATUS,
        #                            SO.CODIGOFL FILIAL,
        #                            SO.USUARIO SOLICITANTE,
        #                            CC.EMAIL
        #                     FROM
        #                         CPR_SOLICITACAO SO, 
        #                         CPR_ITENSSOLICITADOS CIS,
        #                         EST_CADMATERIAL CM,
        #                         CTR_CADASTRODEUSUARIOS CC
        #                     WHERE
        #                             SO.CODIGOEMPRESA = {empresa}
        #                         AND
        #                         	SO.CODIGOFL = {fil}                  
        #                         AND
        #                         	SO.NUMEROSOLIC = CIS.NUMEROSOLIC 
        #                         AND
        #                         	SO.STATUSSOLIC = 'P'                      
        #                         AND    
        #                         	SO.DATASOLIC BETWEEN ((SYSDATE)-30) AND (SYSDATE) 
        #                         AND    
        #                         	CM.CODIGOMATINT = CIS.CODIGOMATINT                
        #                         AND
        #                         	SO.NUMEROSOLIC = {idsolic}                        
        #                         AND
        #                         	CC.USUARIO = SO.USUARIO
        #                     GROUP BY
        #                           SO.NUMEROSOLIC,
        #                           CM.DESCRICAOMAT,
        #                           SO.DATASOLIC,
        #                           CIS.QTDEITSOLIC,
        #                           SO.STATUSSOLIC,
        #                           SO.CODIGOEMPRESA,
        #                           SO.CODIGOFL,
        #                           SO.USUARIO,
        #                           CC.EMAIL
        #                     UNION ALL                        
        #                     SELECT 
        #                            SO.NUMEROSOLIC NR_SOLICITACAO,
        #                            SCO.DESCRICAOSOLOUTROS PRODUTO,
        #                            SO.DATASOLIC DATA,
        #                            SCO.QTDESOLOUTROS QTD_ITENS,
        #                            CASE
        #                                WHEN SO.STATUSSOLIC = 'A' THEN 'ABERTO'
        #                                WHEN SO.STATUSSOLIC = 'P' THEN 'APROVADO'
        #                                WHEN SO.STATUSSOLIC = 'F' THEN 'FECHADO'
        #                            END STATUS,
        #                            SO.CODIGOFL FILIAL,
        #                           SO.USUARIO SOLICITANTE,
        #                            CC.EMAIL
        #                     FROM
        #                         CPR_SOLICITACAO SO,
        #                         CPR_SOLICOUTROS SCO,
        #                         CTR_CADASTRODEUSUARIOS CC
        #                     WHERE
        #                             SO.CODIGOEMPRESA = {empresa}
        #                         AND
        #                     		SO.CODIGOFL = {fil}                
        #                     	AND
        #                         	SO.NUMEROSOLIC = SCO.NUMEROSOLIC                  
        #                         AND
        #                         	SCO.STATUSSOLOUTROS = 'P'                         
        #                         AND    
        #                         	SO.DATASOLIC BETWEEN ((SYSDATE)-30) AND (SYSDATE) 
        #                         AND
        #                         	SO.NUMEROSOLIC = {idsolic}                        
        #                         AND
        #                         	CC.USUARIO = SO.USUARIO                           
        #                     GROUP BY
        #                           SO.NUMEROSOLIC,
        #                           SCO.DESCRICAOSOLOUTROS,
        #                           SCO.QTDESOLOUTROS,
        #                           SO.DATASOLIC,
        #                           SO.STATUSSOLIC,
        #                           SO.CODIGOEMPRESA,
        #                           SO.CODIGOFL,
        #                           SO.USUARIO,
        #                           CC.EMAIL
        #                     """)
        #     except cxerr:
        #         print('CHEGOU NO FINAL DA QUERY')
        #         messages.error(request, 'Não encontrado solicitação com este número.')
        #     except Exception as e:
        #         print('AQUI É o EROOO===',e)
        #         messages.error(f'Error:{e}, error_type:{type(e).__name__}')
        #     else:
        #         print('feching results...')
        #         print('Entrou no ELSE')
        #         res = dictfetchall(cur)
        #         cur.close()
        #         print('AQUI É o RES: ',res)
        #         if res:
        #             print(res)
        #             for q in res:
    if request.method == 'POST':
        idsolic = request.POST.get('getid')
        empresa = request.POST.get('empresa')
        fil = request.POST.get('filial')
        anexo = request.FILES.get('getanexo')

        usuario: list[User] = User.objects.filter(id=request.user.id)
        if usuario:
            username = usuario[0].username.split(".")[0].upper()
            email = usuario[0].email
        if idsolic:
            try:
                filial = Filiais.objects.filter(id_empresa=empresa, id_filial=fil).first()
                obj = SolicitacoesCompras.objects.create(
                    nr_solic=int(idsolic), data=datetime.datetime.now(), status="ANDAMENTO",
                    filial=filial, empresa=empresa, codigo_fl = fil, autor=request.user, anexo=anexo,
                    solicitante=username or None, email_solic=email or None
                )
                obj.save()
                messages.success(request, f'Solicitação cadastrada com sucesso!')
            except Exception as e:
                print('AQUI É o EROOO===',e)
                # messages.error(request, f'Error:{e}, error_type:{type(e).__name__}')
                messages.error(request, f'{filial}')
        else:
            messages.error(request, 'Não encontrado solicitação com este número.')
        return redirect('portaria:compras_index')


def compras_lancar_pedido_temp(request):
    keyga = {v: k for k, v in GARAGEM_CHOICES}
    gakey = {k: v for k, v in GARAGEM_CHOICES}
    if request.method == 'POST':
        print('compras lancar pedido temporario')
        idsolic = request.POST.get('getid')
        empresa = request.POST.get('empresa')
        fil = request.POST.get('filial')
        anexo = request.FILES.get('getanexo')
        if idsolic:
            print(f'gakey: {gakey[empresa+fil]}')
            try:
                obj = SolicitacoesCompras.objects.get(nr_solic=idsolic)
            except ObjectDoesNotExist:
                obj = SolicitacoesCompras.objects.create(
                    nr_solic=idsolic, 
                    filial= (empresa+fil), 
                    empresa= empresa,
                    codigo_fl = fil,
                    autor=request.user, 
                    anexo=anexo
                )
                obj.anexo = anexo
                obj.ultima_att = request.user
                obj.save()
            messages.success(request, f'Solicitação cadastrada com sucesso!')
    return redirect('portaria:compras_index')

def compras_lancar_direto(request):
    keyga = GARAGEM_CHOICES
    gakey = {k: v for k, v in GARAGEM_CHOICES}
    deps = DEPARTAMENTO_CHOICES
    if request.method == 'POST':
        compras = SolicitacoesCompras.objects.all()
        idsolic = f'm{compras.count()}' #id aleatório de solicitação
        data = request.POST.get('data')
        fil = request.POST.get('filial')
        categoria = request.POST.get('categoria')
        solicitante = request.POST.get('solic')
        email_solic = request.POST.get('email')
        departamento = request.POST.get('dep')
        anexo = request.FILES.get('getanexo')
        p_item = request.POST.get('p_item')
        p_qty = request.POST.get('p_qty')
        try:
            print(idsolic, data, fil, categoria, solicitante, email_solic, departamento, anexo, p_item, p_qty)
            obj = SolicitacoesCompras.objects.create(
                nr_solic=idsolic, 
                data=data, 
                status='CONCLUIDO',
                codigo_dl = fil,
                filial=gakey[fil],
                categoria=categoria,
                solicitante=solicitante, 
                autor=request.user,
                departamento=departamento, 
                email_solic=email_solic, 
                anexo=anexo
            )
            prod = ProdutosSolicitacoes.objects.create(
                produto=p_item,
                qnt_itens=int(p_qty),
                solic_ref=obj
            )

        except:
            messages.error(request, f'Erro ao criar a Solicitação, por favor verifique os dados')
    return render(request, 'portaria/etc/lancardireto.html', {'filiais': keyga, 'deps': deps})

def garagem_para_filial_praxio(garagem):
    if garagem == 'SPO':
        newga = {'empresa':'1', 'filial': '1'  } 
    elif garagem == 'REC':  
        newga = {'empresa':'1', 'filial': '2'  } 
    elif garagem == 'SSA':  
        newga = {'empresa':'1', 'filial': '3'  } 
    elif garagem == 'FOR':
        newga = {'empresa':'1', 'filial': '4'  } 
    elif garagem == 'MCZ':  
        newga = {'empresa':'1', 'filial': '5'  } 
    elif garagem == 'NAT':  
        newga = {'empresa':'1', 'filial': '6'  } 
    elif garagem == 'JPA':  
        newga = {'empresa':'1', 'filial': '7'  } 
    elif garagem == 'AJU':  
        newga = {'empresa':'1', 'filial': '8'  } 
    elif garagem == 'VDC':
        newga = {'empresa':'1', 'filial': '9'  } 
    elif garagem == 'CTG': 
        newga = {'empresa':'1', 'filial': '10' } 
    elif garagem == 'GVR':
        newga = {'empresa':'1', 'filial': '11' } 
    elif garagem == 'VIX':
        newga = {'empresa':'1', 'filial': '12' } 
    elif garagem == 'TCO':                        
        newga = {'empresa':'1', 'filial': '13' } 
    elif garagem == 'UDI': 
        newga = {'empresa':'1', 'filial': '14' } 
    elif garagem == 'VIX':
        newga = {'empresa':'1', 'filial': '50' } 
    elif garagem == 'SPO':
        newga = {'empresa':'1', 'filial': '20' } 
    elif garagem == 'SPO':
        newga = {'empresa':'1', 'filial': '21' } 
    elif garagem == 'CTG':
        newga = {'empresa':'2', 'filial': '20' } 
    elif garagem == 'TCO':
        newga = {'empresa':'2', 'filial': '21' } 
    elif garagem == 'UDI':                        
        newga = {'empresa':'2', 'filial': '22' } 
    elif garagem == 'TMA':
        newga = {'empresa':'2', 'filial': '23' } 
    elif garagem == 'VIX':   
        newga = {'empresa':'2', 'filial': '24' } 
    elif garagem == 'VIX':                                
        newga = {'empresa':'2', 'filial': '50' } 
    elif garagem == 'BMA':
        newga = {'empresa':'3', 'filial': '30' } 
    elif garagem == 'BPE':
        newga = {'empresa':'3', 'filial': '31' } 
    elif garagem == 'BEL':    
        newga = {'empresa':'3', 'filial': '32' } 
    elif garagem == 'BPB':
        newga = {'empresa':'3', 'filial': '33' } 
    elif garagem == 'SLZ':
        newga = {'empresa':'3', 'filial': '34' } 
    elif garagem == 'BAL':
        newga = {'empresa':'3', 'filial': '35' } 
    elif garagem == 'THE': 
        newga = {'empresa':'3', 'filial': '36' } 
    elif garagem == 'THE':  
        newga = {'empresa':'3', 'filial': '52' } 
    elif garagem == 'FMA':
        newga = {'empresa':'4', 'filial': '40' } 
    return newga

def painel_compras(request):
    CharField.register_lookup(Lower)
    form = SolicitacoesCompras.objects.all().exclude(Q(status='CONCLUIDO') | Q(status='CANCELADO')).order_by('data')

    if request.method == 'GET':
        filter = request.GET.get('filter')
        filtertype = request.GET.get('filtertype')
        if filter:
            try:
                filter = filter.upper()
                tipo_filtro = {
                    "filial": {"filial": filter},
                    "solicitante": {"solicitante": filter},
                    "codigo": {"nr_solic": filter},
                    "departamento": {"departamento": filter},
                }

                form = SolicitacoesCompras.objects.filter(**tipo_filtro[filtertype]).order_by('pub_date')
            except Exception:
                messages.error(request, 'Selecione algum filtro.')
    return render(request, 'portaria/etc/painelcompras.html', {'form':form})

def painel_compras_concluido(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        if date:
            CharField.register_lookup(Lower)
            form = SolicitacoesCompras.objects.filter(status='CONCLUIDO', data=date).order_by('data')
            if request.method == 'GET':
                filter = request.GET.get('filter')
                filtertype = request.GET.get('filtertype')
                if filter:
                    if filtertype == 'filial':
                        filter = filter.upper()
                        form = SolicitacoesCompras.objects.filter(filial=filter).order_by('pub_date')
                    elif filtertype == 'solicitante':
                        filter = filter.upper()
                        form = SolicitacoesCompras.objects.filter(solicitante=filter).order_by('pub_date')
                    elif filtertype == 'codigo':
                        form = SolicitacoesCompras.objects.filter(nr_solic=filter).order_by('pub_date')
                    elif filtertype == 'departamento':
                        filter = filter.upper()
                        form = SolicitacoesCompras.objects.filter(departamento=filter).order_by('pub_date')
                    else:
                        messages.error(request, 'Selecione algum filtro.')
        print(form)
        return render(request, 'portaria/etc/painelcomprasconcluido.html', {'form':form})
    else:
        print('aaaa')

def page_disabled(request, id):
    return render(request, 'portaria/etc/page_disabled.html')

def edit_compras(request, id):
    editor = TextEditor()
    obj = get_object_or_404(SolicitacoesCompras, id=id)
    # obj = SolicitacoesCompras.objects.get(id=int(id))
    entradas = SolicitacoesEntradas.objects.filter(cpr_ref=obj)
    filchoices = FILIAL_CHOICES
    empchoices = EMPRESA_CHOICES
    filkey = {v:k for v,k in filchoices}
    empkey = {v:k for v,k in empchoices}
    stschoices = SolicitacoesCompras.STATUS_CHOICES
    dpchoices = SolicitacoesCompras.DEPARTAMENTO_CHOICES
    pgtchoices = SolicitacoesCompras.FORMA_PGT_CHOICES
    rpchoices = User.objects.filter(groups__name='compras').exclude(id=1)
    print(f'obj: {obj.data} | email_solic: {obj.email_solic}')
    if request.method == 'POST':
        status = request.POST.get('status')
        departamento = request.POST.get('departamento')
        responsavel = request.POST.get('responsavel')
        categoria = request.POST.get('categoria')
        forma_pgt = request.POST.get('forma_pgt')
        prazo = request.POST.get('prazo_conclusao')
        dt_venc = request.POST.get('dt_venc')
        get_anexo = request.FILES.get('getanexo')
        textarea = request.POST.get('area')
        obs = request.POST.get('obs')
        files = request.FILES.getlist('file')
        pago = request.POST.get('pago')
        try:
            if status != '':
                obj.status = status
                messages.success(request, f'Status alterado para {status} com sucesso!')
            #if empresa != '': obj.empresa = empresa
            #if filial != '': obj.filial = filial
            if departamento != '': obj.departamento = departamento
            if forma_pgt != '': obj.forma_pgt = forma_pgt
            if responsavel != '': obj.responsavel_id = responsavel
            if categoria != '': obj.categoria = categoria
            if get_anexo != '' and bool(get_anexo) is True: obj.anexo = get_anexo
            if dt_venc != '' and dt_venc is not None: obj.dt_vencimento = dt_venc
            if prazo != '' and prazo is not None: obj.prazo_conclusao = prazo
            if obs != '' and obs is not None: obj.obs = obs
            if textarea and textarea != '<p><br></p>': insert_entradas_cpr(request, obj, textarea, files)
            if obj.pago != pago and pago is not None: obj.pago = pago


            entradas = SolicitacoesEntradas.objects.filter(cpr_ref=obj)
            resp = ""
            if obj.responsavel: resp = obj.responsavel.first_name
            corpo_email = {
                "subject": f"Atualização da Solicitação: {obj.nr_solic}",
                "status": obj.status,
                "departamento": obj.departamento,
                "responsavel": resp,
                "categoria": obj.categoria,
                "data": obj.pub_date.strftime('%d-%m-%Y'),
                "nr_pedido": obj.nr_solic,
                "email_solicitante": obj.email_solic,
                "observacao": obj.obs,
                "entradas": entradas,
            }
            # envio = envia_email(corpo_email)
            # if envio: messages.info(request, f'Email enviado com sucesso!')
            # else: messages.info(request, f'Ocorreu uma falha ao enviar o email')

        except Exception as e:
            print(f'err:{e}, err_t:{type(e).__name__}')
            raise e
        else:
            try:

                obj.ultima_att = request.user
                obj.save()
                print('novo objeto: ', obj.departamento)
                messages.info(request, f'Solicitação {obj.nr_solic} alterada com sucesso')
                return redirect('portaria:painel_compras')
            except Exception as e:
                print(f'err: {e}, err_type:{type(e).__name__}')
                return redirect('portaria:painel_compras')
    try:
        vencimento = (obj.dt_vencimento - datetime.date.today()).days
    except:
        vencimento = None

    print(f'{obj.departamento} | {obj.dt_vencimento} | obj.pago')

    return render(request, 'portaria/etc/edit_compras.html', {'obj':obj, 'filchoices':filchoices, 'stschoices':stschoices,
                                                              'dpchoices':dpchoices, 'rpchoices':rpchoices, 'empchoices': empchoices,
                                                              'entradas':entradas, 'editor':editor, 'vencimento': vencimento})

def insert_entradas_cpr(request, obj, textarea, files):
    if obj:
        try:
            entrada = {
                "obs": textarea,
                "cpr_ref": obj,
                "ultima_att": request.user
            }
            if len(files) > 0:   
                for index in range(len(files)):
                    entrada[f"file{index + 1}"] = files[index]

            SolicitacoesEntradas.objects.create(**entrada)
        except Exception as e:
            print(f'Error:{e}, error_type:{type(e).__name__}')
            messages.error(request,'Ops, algo deu errado :(')
            raise e
        messages.success(request, 'Cadastrado com sucesso :)')
        # else:
        #     file1 = None
        #     file2 = None
        #     file3 = None
        #     itens = [i.produto for i in obj.produtossolicitacoes_set.all()]
        #     text = f'''
        #         Solicitação: {obj.nr_solic} <br>
        #         Categoria: {obj.categoria} <br>
        #         Data: {obj.data} <br>
        #         Status: {obj.status} <br>
        #         Responsável: {obj.responsavel} <br>
        #         Itens solicitados:<br>
        #     '''
        #     for q in itens:
        #         text += f'{q} <br>'
        #     text += f'{entrada.obs}'
        #     if entrada.file1:
        #         file1 = entrada.file1
        #     if entrada.file2:
        #         file2 = entrada.file2
        #     if entrada.file3:
        #         file3 = entrada.file3
        #     text += '<br>Atenciosamente,<br>Bora Desenvolvimento.'
        #     try:
        #         sendmail_compras(obj.email_solic, text, file1=file1, file2=file2, file3=file3)
        #     except:
        #         pass

def sendmail_compras(to, text, file1, file2, file3):
    fromm = 'bora@bora.tec.br' ########### alterar
    msg = MIMEMultipart()
    msg['From'] = fromm
    msg['To'] = to
    msg['Subject'] = f'Nova entrada da solicitação de compras'
    msg.attach(MIMEText(text, 'html', 'utf-8'))
    if file1:
        data = file1.read()
        part = MIMEApplication(data, str(os.path.basename(file1.name)))
        part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(file1.name)
        msg.attach(part)
    if file2:
        data = file2.read()
        part = MIMEApplication(data, str(os.path.basename(file2.name)))
        part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(file2.name)
        msg.attach(part)
    if file3:
        data = file3.read()
        part = MIMEApplication(data, str(os.path.basename(file3.name)))
        part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(file3.name)
        msg.attach(part)
    sm = smtplib.SMTP('smtp.kinghost.net', '587')
    sm.set_debuglevel(1)
    sm.login(fromm, "Bor@dev#123")
    sm.sendmail(fromm, to, msg.as_string())

'''def terceirizados_index(request):
    return render(request, 'portaria/etc/terceirizadosindex.html')

def insert_terceirizados(request):
    forns = FornecedorTerceirizados.objects.all()
    form = InsertTerceirizados
    autor = request.user
    keyga = {v: k for k, v in GARAGEM_CHOICES}
    if request.method == 'POST':
        form = InsertTerceirizados(request.POST or None)
        if form.is_valid():
            try:
                foto = request.FILES.get('foto')
                nome_f = form.cleaned_data['nome_funcionario']
                forn = form.cleaned_data['fornecedor']
                nforn = FornecedorTerceirizados.objects.get(razao_social=forn)
                order = form.save(commit=False)
                order.autor = autor
                order.foto = foto
                order.filial = keyga[autor.last_name]
                order.valor = nforn.valor_p_funcionario
                order.save()
            except Exception as e:
                print(f'Error: {e}, error_type: {type(e).__name__}')
                raise e
            else:
                messages.success(request, f'{nome_f} cadastrado com sucesso')
                return redirect('portaria:terceirizadosindex')

    return render(request, 'portaria/etc/insertterceirizados.html', {'form':form, 'forns':forns})

def saidas_terceirizados(request):
    obj = RegistraTerceirizados.objects.filter(data_saida__isnull=True)
    if request.method == 'POST':
        aa = request.POST.get('funcid')
        try:
            RegistraTerceirizados.objects.filter(pk=aa).update(data_saida=timezone.now())
        except Exception as e:
            print(f'Error: {e}, error_type: {type(e).__name__}')
            messages.error(request,'Whoops, something went wrong!')
            return redirect('portaria:saidas_terceirizados')
        else:
            messages.success(request, f'inserido com sucesso')
            return redirect('portaria:saidas_terceirizados')
    return render(request, 'portaria/etc/saidasterceirizados.html', {'obj':obj})

def get_terceirizados_xls(request):
    array = []
    if request.method == 'POST':
        date1 = datetime.datetime.strptime(request.POST.get('date1'), '%Y-%m-%d')
        date2 = datetime.datetime.strptime(request.POST.get('date2'), '%Y-%m-%d').replace(hour=23, minute=59)
        qs = RegistraTerceirizados.objects.filter(data_entrada__lte=date2, data_entrada__gte=date1)
        if qs:
            for q in qs:
                array.append({'FILIAL': q.get_filial_display(), 'FORNECEDOR': q.fornecedor, 'NOME': q.nome_funcionario,
                              'RG': q.rg,'CPF': q.cpf,'VALOR': q.valor,'DATA_ENTRADA': dateformat.format(q.data_entrada, 'd-m-Y H:i'),
                              'DATA_SAIDA':dateformat.format(q.data_saida, 'd-m-Y H:i'),'AUTOR': q.autor})
            df = pd.DataFrame(array)
            buffer = io.BytesIO(df.to_string().encode('utf-8'))
            df.to_excel(buffer, engine='xlsxwriter', index=False)
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename=relatorio-terceirizados-{datetime.date.today()}.xlsx'
            writer = pd.ExcelWriter(response, engine='xlsxwriter')
            df.to_excel(writer, 'sheet1', index=False)
            writer.save()
            return response'''

def sugestoesedenuncias(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        texto = request.POST.get('texto')
        categoria = request.POST.get('categoria')
        identificacao = request.POST.get('iden')
        if title and texto and categoria:
            obj = Sugestoes.objects.create(titulo=title, texto=texto, categoria=categoria)
            if request.FILES.get('anexo'):
                obj.file = request.FILES.get('anexo')
            if identificacao:
                obj.autor = identificacao
            obj.save()
            messages.success(request, 'Success')
            return redirect('portaria:sugestoesedenuncias')
        else:
            messages.error(request, 'Error')
            return redirect('portaria:sugestoesedenuncias')
    return render(request, 'portaria/etc/sugestoesedenuncias.html')

def estoque_index(request):
    if request.method == 'POST':
        itens_r = request.POST.get('itens')
        itens_r = itens_r.split(',')
        print(f'Itens_r: {itens_r}')
        itens = {}
        for count, i in enumerate(itens_r):
            c = i.split(' ')
            itens[int(c[0])] = int(c[1])
        print(itens)
    solic = EstoqueSolicitacoes.objects.filter(data_envio__isnull=True)
    metrics = EstoqueSolicitacoes.objects.annotate(
        aberto=Count('id', filter=Q(data_envio__isnull=True)),
        ag_conf=Count('id', filter=Q(data_envio__isnull=False, confirmacao=None)),
        concluido=Count('id', filter=Q(confirmacao__isnull=False))
    ).aggregate(aberto1=Sum('aberto'),ag_conf1=Sum('ag_conf'), concluido1=Sum('concluido'))
    itens_solicitados = {}
    carts = Cart.objects.filter(solic__in = solic)
    cart_item = CartItem.objects.filter(cart__in = carts).order_by('desc')
    for i in cart_item:
        itens_solicitados[str(f"{i.desc} - {i.tam}")] = i.qty
    
    return render(request, 'portaria/estoque/estoqueindex.html', {'solics': solic, 'metrics':metrics, 'itens_solicitados': itens_solicitados})

def estoque_painel(request):
    form = EstoqueSolicitacoes.objects.filter(data_envio__isnull=True)
    return render(request, 'portaria/estoque/painelsolic.html', {'form':form})

def estoque_confirma_item(request):
    form = EstoqueSolicitacoes.objects.filter(data_envio__isnull=False, confirmacao=None)
    if request.method == 'GET':
        busca = request.GET.get('buscaitem')
        if busca:
            form = EstoqueSolicitacoes.objects.filter(data_envio__isnull=False, confirmacao=None, pk=busca)
    if request.method == 'POST':
        obj = request.POST.get('objid')
        try:
            obj = get_object_or_404(EstoqueSolicitacoes, pk=obj)
            # Remover itens
            for cart in obj.cart_set.all():
                for ci in cart.cartitem_set.all():
                    tamanho = Tamanho.objects.get(id=ci.tam_id)
                    if tamanho.quantidade < ci.qty:
                        messages.error(request, f'O item {ci.desc} - {ci.tam} está em falta. (Solicitado: {ci.qty} | Em estoque: {tamanho.quantidade} ')

                        return redirect('portaria:estoque_confirma_item')
            for cart in obj.cart_set.all():
                for ci in cart.cartitem_set.all():
                    print(ci.desc, ci.tam, ci.qty)
                    item = Item.objects.filter(desc = ci.desc).first()
                    print(item.desc, item.id)
                    Tamanho.objects.filter(id=ci.tam_id).update(quantidade=F('quantidade') - ci.qty)
                    tam = Tamanho.objects.get(id=ci.tam_id)
                    print(tam.quantidade)

        except Exception as e:
            print(e)
        else:
            obj.confirmacao = timezone.now()
            obj.autor_confirmacao = request.user
            obj.save()
            messages.success(request, 'Solicitação com id %s confirmada com sucesso.' % obj.id)
    return render(request, 'portaria/estoque/confirmasolicitacao.html', {'form':form})

def estoque_nova_solic(request):
    tipoga = {k: v for k, v in TIPO_GARAGEM}
    itens = EstoqueItens.objects.all()
    
    filiais = TIPO_GARAGEM
    if request.method == 'POST':
        fil = request.POST.get('filial')
        itens_re = request.POST.get('itensInput')
        colab = request.POST.get('colab')
        print(fil, itens_re)
        obj = EstoqueSolicitacoes.objects.create(filial=tipoga[fil], colab=colab, data_solic=timezone.now(), autor=request.user)
        cart = Cart.objects.create(solic=obj)

        itens = itens_re[:-1]
        itens = itens.split(',')
        for it in itens:
            i = it.split(' ')
            print(i)
            tam = Tamanho.objects.get(id=int(i[0]))
            CartItem.objects.create(cart=cart, tam_id=tam.id, desc=tam.item.desc, ca=tam.item.ca, tam=tam.tam, qty=int(i[1]))

        return redirect('portaria:estoque_index')
    return render(request, 'portaria/estoque/nova_solicitacao.html', {'itens':itens, 'filiais':filiais})

def estoque_listagem_itens(request):
    itens = EstoqueItens.objects.all().order_by('grupo')
    if request.method == 'GET':
        item = request.GET.get('buscaitem')
        if item:
            itens = EstoqueItens.objects.filter(grupo__contains=item)

    if request.method == 'POST':
        if request.POST.get('type') == 'GROUP':
            group_name = request.POST.get('name')
            if group_name != '':
                EstoqueItens.objects.create(grupo=group_name)
                messages.success(request, f'grupo {group_name} adicionado com sucesso! ')
            else:
                messages.error(request, 'O nome do grupo não pode ficar em branco')

        if request.POST.get('type') == 'TAM':
            item_id = request.POST.get('item')
            tam = request.POST.get('tam')
            qty = request.POST.get('qty')
            item = Item.objects.get(id=int(item_id))
            Tamanho.objects.create(tam=tam, quantidade=qty, item=item)
            messages.success(request, 'Tamanho adicionado com sucesso!')

        if request.POST.get('type') == 'ITEM':
            estoque = request.POST.get('obj')
            desc = request.POST.get('desc')
            ca = request.POST.get('ca')
            validade = request.POST.get('validade')
            estq = EstoqueItens.objects.get(id=int(estoque))
            Item.objects.create(desc=desc, estoque=estq, ca=ca, validade=validade)
            messages.success(request, 'Item adicionado com sucesso!')

        if request.POST.get('type') == 'EDITTAM':
            tam_id = request.POST.get('item')
            tam = request.POST.get('tam')
            qty = request.POST.get('qty')
            print(f'id: {tam_id} tam: {tam} qty: {qty} ')
            Tamanho.objects.filter(id=int(tam_id)).update(tam=tam, quantidade=qty)
            messages.success(request, 'Tamanho ajustado com sucesso!')
            
        return redirect('portaria:estoque_listagem_itens')
        
    return render(request, 'portaria/estoque/itens_index.html', {'itens': itens})

def estoque_detalhe(request, id):
    editor = TextEditor()
    item = get_object_or_404(EstoqueSolicitacoes, pk=id)
    if request.method == 'POST':
        area = request.POST.get('area')
        e_to = request.POST.get('e_to')

        if area and area != '<p><br></p>' and e_to:
            if request.POST.get('file') != '':
                myfile = request.FILES.getlist('file')
            else:
                myfile = None
                items = ''
            for cart in item.cart_set.all():
                for i in cart.cartitem_set.all():
                    items += f'''
                        <tr>
                            <td style="text-align: center; padding: 0 5px;"> {i.desc} </td>
                            <td style="text-align: center; padding: 0 5px;"> {i.ca} </td>
                            <td style="text-align: center; padding: 0 5px;"> {i.tam} </td>
                            <td style="text-align: center; padding: 0 5px;"> {i.qty} </td>
                        </tr>

                    '''
            area += f'''
                <table>
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>CA</th>
                            <th>Tamanho</th>
                            <th>Quantidade</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items}
                    <tbody>
                </table>
                <br>
                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                    <tr>
                        <td>
                            <table border="0" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td bgcolor="#3485FF" style="padding: 4px 16px; border-radius:4px">
                                        <a href="{request.build_absolute_uri(reverse('portaria:estoque_confirma_item'))}?buscaitem={item.id}" target="_blank" style="font-size: 16px; mso-line-height-rule:exactly; line-height: 16px; font-family: 'Cabin',Arial, Helvetica, sans-serif; font-weight: 100; letter-spacing:0.025em; color: #ffffff; text-decoration: none; display: inline-block;">Confirmar solicitação</a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            '''
            msg = MIMEMultipart()
            if myfile is not None:
                for q in myfile:
                    q.seek(0)
                    part = MIMEApplication(q.file.getvalue(), name=str(q.open()))
                    msg.attach(part)
            msg['Subject'] = f'Solicitação Compras {item.colab}'
            msg['From'] = 'envio@bora.com.br'
            msg['To'] = e_to
            msg.attach(MIMEText(area, 'html', 'utf-8'))
            smtp_h = 'smtp.kinghost.net'
            smtp_p = '587'
            user = 'bora@bora.tec.br'
            passw = get_secret('EPASS_CH')
            try:
                sm = smtplib.SMTP(smtp_h, smtp_p)
                sm.set_debuglevel(1)
                sm.login(user, passw)
                sm.sendmail(user, e_to, msg.as_string())
                item.data_envio = timezone.now()
                item.save()

            except Exception as e:
                print(f'ErrorType:{type(e).__name__}, Error:{e}')
                raise e
            else:
                messages.success(request, 'Resposta enviada com sucesso!')
                return redirect('portaria:estoque_index')
        else:
            messages.error(request, 'Algo deu errado, gentileza verifique os parâmetros.')

    return render(request, 'portaria/estoque/detalhesolic.html', {'editor': editor, 'obj':item})

def estoque_caditem(request):
    if request.method == 'POST':
        desc = request.POST.get('desc')
        qnt = request.POST.get('qnt')
        tipo = request.POST.get('tipo')
        tam = request.POST.get('tam')
        if desc and qnt and tipo and tam:
            try:
                desc = desc.upper()
                qnt = int(qnt)
                tipo = tipo.upper()
                tam = tam.upper()
                obj = get_object_or_404(EstoqueItens, desc=desc, tamanho=tam)
            except Http404:
                EstoqueItens.objects.create(desc=desc, tamanho=tam, quantidade=qnt, tipo=tipo)
                messages.success(request, 'Item cadastrado com sucesso !!')
            except Exception as e:
                messages.error(request, 'Algo deu errado, por gentileza verifique os parâmetros.')
                print(e)
            else:
                messages.warning(request, 'Item já cadastrado!')
        else:
            messages.error(request, 'Está faltando informações, gentileza verificar.')
    return render(request, 'portaria/estoque/cadastroitem.html')
"""
def estoque_listagem_itens(request):
    form = EstoqueItens.objects.all().order_by('desc')
    autocomplete = EstoqueItens.objects.all()
    if request.method == 'GET':
        item = request.GET.get('buscaitem')
        if item:
            form = EstoqueItens.objects.filter(desc=item)
    if request.method == 'POST':
        obj = request.POST.get('obj')
        qnt = int(request.POST.get('quantidade'))
        if obj and qnt > 0:
            try:
                obj = get_object_or_404(EstoqueItens, pk=obj)
            except Exception as e:
                print(e)
            else:
                obj.quantidade += qnt
                messages.success(request, 'Quantidade do %s alterado para %s' % (obj, obj.quantidade))
                obj.save()
    return render(request, 'portaria/estoque/listagemitens.html', {'form':form, 'autocomplete':autocomplete})

def estoque_detalhe(request, id):
    editor = TextEditor()
    obj = get_object_or_404(EstoqueSolicitacoes, pk=id)
    if request.method == 'POST':
        area = request.POST.get('area')
        e_to = request.POST.get('e_to')

        if area and area != '<p><br></p>' and e_to:
            if request.POST.get('file') != '':
                myfile = request.FILES.getlist('file')
            else:
                myfile = None
            area += f'''
                <br>
                <a href="http://localhost:8000/estoque/confirma?buscaitem={obj.id}">
                <button>Confirmar solicitação</button>
                </a>
            '''
            msg = MIMEMultipart()
            if myfile is not None:
                for q in myfile:
                    q.seek(0)
                    part = MIMEApplication(q.file.getvalue(), name=str(q.open()))
                    msg.attach(part)
            msg['Subject'] = 'Solicitação Compras %s %s' % (obj.item, obj.item.tamanho)
            msg['From'] = 'envio@bora.com.br'
            msg['To'] = e_to
            msg.attach(MIMEText(area, 'html', 'utf-8'))
            smtp_h = 'smtp.bora.com.br'
            smtp_p = '587'
            passw = 'B0r*520150'
            try:
                sm = smtplib.SMTP(smtp_h, smtp_p)
                sm.set_debuglevel(1)
                sm.login('envio@bora.com.br', passw)
                sm.sendmail('envio@bora.com.br', e_to, msg.as_string())
                obj.data_envio = timezone.now()
                obj.save()
            except Exception as e:
                print(f'ErrorType:{type(e).__name__}, Error:{e}')
                raise e
            else:
                messages.success(request, 'Resposta enviada com sucesso!')
                return redirect('portaria:estoque_index')
        else:
            messages.error(request, 'Algo deu errado, gentileza verifique os parâmetros.')
    return render(request, 'portaria/estoque/detalhesolic.html', {'editor':editor, 'obj':obj})

def estoque_caditem(request):
    if request.method == 'POST':
        desc = request.POST.get('desc')
        qnt = request.POST.get('qnt')
        tipo = request.POST.get('tipo')
        tam = request.POST.get('tam')
        if desc and qnt and tipo and tam:
            try:
                desc = desc.upper()
                qnt = int(qnt)
                tipo = tipo.upper()
                tam = tam.upper()
                obj = get_object_or_404(EstoqueItens, desc=desc, tamanho=tam)
            except Http404:
                EstoqueItens.objects.create(desc=desc, tamanho=tam, quantidade=qnt, tipo=tipo)
                messages.success(request, 'Item cadastrado com sucesso !!')
            except Exception as e:
                messages.error(request, 'Algo deu errado, por gentileza verifique os parâmetros.')
                print(e)
            else:
                messages.warning(request, 'Item já cadastrado!')
        else:
            messages.error(request, 'Está faltando informações, gentileza verificar.')
    return render(request, 'portaria/estoque/cadastroitem.html')
"""
def index_demissoes(request):
    if request.method == 'GET':
        cpf = request.GET.get('getcpf')
        if cpf:
            try:
                obj = get_object_or_404(Demissoes, cpf=cpf)
            except Exception as e:
                messages.error(request, 'Erro: não encontrado o CPF -- %s' % e)
                return render(request, 'portaria/pj/index_demissoes.html')
            else:
                return render(request, 'portaria/pj/index_demissoes.html', {'obj':obj})

    if request.method == 'POST':
        data = request.POST.get('datademissao')
        motivo = request.POST.get('motivo')
        cpf = request.POST.get('getcpf')
        update_demissoes(request, cpf, data, motivo)
    return render(request, 'portaria/pj/index_demissoes.html')

def checa_demissoes(request, cpf):
    try:
        obj = get_object_or_404(Demissoes, cpf=cpf)
    except Exception as e:
        error = messages.error(request, 'Erro: não encontrado o CPF -- %s' % e)
        return error
    else:
        return obj

def update_demissoes(request, cpf, data, motivo):
    try:
        obj = get_object_or_404(Demissoes, cpf=cpf)
    except Exception as e:
        messages.error(request, 'Erro: não encontrado o CPF -- %s' % e)
    else:
        obj.dtdemissao = data
        obj.motivodemissao = motivo
        obj.save()
        messages.success(request, 'Cadastrado com sucesso!')

def get_funcionarios_demissao(request):
    conn = conndb()
    cur = conn.cursor()
    try:
        cur.execute(f"""
                    SELECT 
                           FF.CODIGOEMPRESA,
                           FF.CODIGOFL,
                           FF.NOMEFUNC,
                           FD.NRDOCTO,
                           FF.DTADMFUNC,
                           FF.SITUACAOFUNC
                    FROM 
                           FLP_FUNCIONARIOS FF,
                           FLP_DOCUMENTOS FD
                    WHERE
                           FF.SITUACAOFUNC = 'D'         AND
                           FF.CODIGOEMPRESA <> '999'     AND
                           FF.CODINTFUNC = FD.CODINTFUNC AND
                           FD.TIPODOCTO = 'CPF'
                                """)
    except cxerr as e:
        print(f'Error:{e}, error_type:{type(e).__name__}')
    except Exception as e:
        print(f'Error:{e}, error_type:{type(e).__name__}')
    else:
        res = dictfetchall(cur)
        cur.close()
    for q in res:
        try:
            obj = get_object_or_404(Demissoes, cpf=q['nrdocto'])
        except Http404:
            obj = Demissoes.objects.create(empresa=q['codigoempresa'],filial=q['codigofl'], nome=q['nomefunc'],
                                           cpf=q['nrdocto'], dtadmissao=q['dtadmfunc'])
        except Exception as e:
            print(f'Error:{e}, error_type:{type(e).__name__}')
    return HttpResponse('job done')
