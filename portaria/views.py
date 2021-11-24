#imports geral
import csv
import datetime
import email, smtplib
import textwrap
import poplib
from email import policy
import pandas as pd
from email.mime.text import MIMEText
from email.utils import make_msgid

#imports django built-ins
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Count, Sum, F, Q, Value, CharField, DateTimeField, Subquery
from django.db.models.functions import Coalesce, TruncDate, Cast, TruncMinute
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.template.defaultfilters import upper
from django.urls import reverse
from django.utils import timezone
from django.views import generic


#imports django projeto
from .models import * #Cadastro, PaletControl, ChecklistFrota, Veiculos, NfServicoPj
from .forms import * #CadastroForm, isPlacaForm, DateForm, FilterForm, TPaletsForm, TIPO_GARAGEM, ChecklistForm

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
            return render(request, 'portaria/cardusuario.html', {'form':form})
        else:
            form = src1
            return render(request, 'portaria/cardusuario.html',{'form':form})
    return render(request, 'portaria/cardusuario.html', {'form':form})

def card(request, id):
    idcard = get_object_or_404(CardFuncionario, pk=id)
    form = CardFuncionario.objects.get(pk=idcard.id)
    return render(request, 'portaria/card.html', {'form':form})

#views
@login_required
def index(request):
    return render(request, "portaria/index.html")


class Visualizacao(generic.ListView):
    paginate_by = 10
    template_name = 'portaria/visualizacao.html'
    context_object_name = 'lista'
    form = DateForm()

    def get_queryset(self):
        autor = self.request.user
        if autor.is_staff:
            qs = Cadastro.objects.all().filter(hr_chegada__month=datetime.datetime.now().month).order_by('-hr_chegada')
        else:
            qs = Cadastro.objects.all().filter(hr_chegada__month=datetime.datetime.now().month, autor=autor).order_by('-hr_chegada')
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
        return render(request, 'portaria/cadastroentrada.html', {'cadastro': cadastro, 'form': form})
    else:
        auth_message = 'Usuário não autenticado, por favor logue novamente'
        return render(request, 'portaria/cadastroentrada.html', {'auth_message': auth_message})

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
                    return render(request, 'portaria/cadastrosaida.html', {'form':form})
                else:
                    Cadastro.objects.filter(pk=loc_placa.id).update(hr_saida=timezone.now(), destino=q_query, autor=request.user)
                    messages.success(request, 'Saida cadastrada com sucesso.')
                    return HttpResponseRedirect(reverse('portaria:cadastro'))
        return render(request, 'portaria/cadastrosaida.html', {'form':form})
    else:
        auth_message = 'Usuário não autenticado, por favor logue novamente'
        return render(request, 'portaria/cadastrosaida.html', {'auth_message': auth_message})

@login_required
def cadastro(request):
    if request.user.is_authenticated:
        filiais = TIPO_GARAGEM
        return render(request, 'portaria/cadastro.html', {'filiais':filiais})
    else:
        auth_message = 'Usuário não autenticado, por favor logue novamente'
        return render(request, 'portaria/cadastro.html', {'auth_message': auth_message})

@login_required
def outputs(request):
    return render(request, 'portaria/outputs.html')


class PaleteView(generic.ListView):
    paginate_by = 10
    template_name = 'portaria/paletes.html'
    context_object_name = 'lista'

    def get_queryset(self):
        qs = PaleteControl.objects.values("loc_atual").annotate(num_ratings=Count("id"))
        return qs

@login_required
def frota(request):
    form = ChecklistFrota.objects.all()
    if request.method == 'POST':
        mot = request.POST.get('moto_src')
        if mot:
            qs = Motorista.objects.filter(nome__icontains=mot)
            return render(request, 'portaria/frota.html', {'qs':qs})

    if request.method == "GET":
        pla = request.GET.get('placa_')
        mot = request.GET.get('moto_')
        if pla and mot:
            try:
                pla1 = Veiculos.objects.get(prefixoveic=pla)
                mot1 = Motorista.objects.get(pk=mot)
            except ObjectDoesNotExist:
                messages.error(request,'Cadastro não encontrado')
                return render(request, 'portaria/frota.html')
            else:
                return redirect('portaria:checklistfrota', placa_id=pla1, moto_id=mot1.codigomot)
        elif pla and not mot:
            messages.error(request, 'Insira o motorista e selecione')
            return render(request, 'portaria/frota.html')
        elif mot and not pla:
            messages.error(request, 'Insira a placa')
            return render(request, 'portaria/frota.html')
    return render(request, 'portaria/frota.html',{'form':form})

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
    return render(request,'portaria/checklistfrota.html', {'form':form,'pla':pla, 'mot':mot})

def checklistview(request):
    form = ChecklistFrota.objects.all().order_by('-datachecklist')
    return render(request, 'portaria/checklistview.html', {'form':form})

def checklistdetail(request, idckl):
    form = get_object_or_404(ChecklistFrota, pk=idckl)
    return render(request, 'portaria/checklistdetail.html', {'form':form})


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
                return redirect('portaria:index')
    return render(request, 'portaria/cadfuncionariopj.html', {'form':form})

@login_required
def servicospj(request):
    func = request.GET.get('nomefunc')
    array = []
    qnt_funcs = FuncPj.objects.filter(ativo=True).order_by('nome')
    for q in qnt_funcs:
        query = FuncPj.objects.filter(pk=q.id)
        array.extend(query)
    if func:
        cad = FuncPj.objects.all().filter(nome__icontains=func, ativo=True)
        if cad:
            array.clear()
            for c in cad:
                query = FuncPj.objects.filter(pk=c.id)
                array.extend(query)
    return render(request, 'portaria/servicospj.html', {'array': array})

@login_required
def consultanfpj(request):
    arrya = []
    qnt_funcs = FuncPj.objects.filter(ativo=True)
    for q in qnt_funcs:
        query = FuncPj.objects.filter(pk=q.id) \
            .annotate(faculdade=Coalesce(Sum('nfservicopj__faculdade', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month)),Value(0.0)),
            cred_convenio=Coalesce(Sum('nfservicopj__cred_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month)),Value(0.0)),
            outros_cred=Coalesce(Sum('nfservicopj__outros_cred', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month)),Value(0.0)),
            desc_convenio=Coalesce(Sum('nfservicopj__desc_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month)),Value(0.0)),
            outros_desc=Coalesce(Sum('nfservicopj__outros_desc', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month)),Value(0.0)),
            ) \
            .annotate(total=((F('salario') + F('ajuda_custo') + F('faculdade') + F('cred_convenio') + F('outros_cred')) - (F('adiantamento') + F('desc_convenio') + F('outros_desc'))))
        arrya.extend(query)
    return render(request, 'portaria/consultanfpj.html', {'arrya': arrya})

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
    return render(request, 'portaria/cadservicospj.html', {'form':form,'func':func})

def decimopj(request):
    allfunc = FuncPj.objects.filter(ativo=True).annotate(parc1=F('pj13__pgto_parc_1'),parc2=F('pj13__pgto_parc_2')).order_by('nome')
    func = request.GET.get('srcfunc')
    if func:
        allfunc = FuncPj.objects.filter(nome__icontains=func, ativo=True).annotate(parc1=F('pj13__pgto_parc_1'),parc2=F('pj13__pgto_parc_2')).order_by('nome')
        return render(request, 'portaria/decimopj.html', {'allfunc': allfunc})
    return render(request,'portaria/decimopj.html', {'allfunc':allfunc})

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
    return render(request, 'portaria/caddecimo1.html', {'func': func})

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
        return render(request, 'portaria/caddecimo2.html', {'func': func, 'form': form})

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
            return render(request, 'portaria/decimoview.html', {'allfuncs': allfuncs, 'array': array})
        elif period == 'pgto_parcela_2':
            array = []
            allfuncs = FuncPj.objects.filter(ativo=True, pj13__pgto_parc_2__isnull=False)
            for q in allfuncs:
                query = FuncPj.objects.filter(pk=q.id).annotate(valor=F('pj13__valor'),
                                                                parc_1=F('pj13__pgto_parc_1'),
                                                                parc_2=F('pj13__pgto_parc_2'),
                                                                periodo=F('pj13__periodo_meses'))
                array.extend(query)
            return render(request, 'portaria/decimoview.html', {'allfuncs': allfuncs, 'array': array})
    return render(request, 'portaria/decimoview.html')

def feriaspjv(request):
    return render(request,'portaria/feriaspj.html')

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

    return render(request,'portaria/feriascad.html', {'form':form})

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
                return render(request, 'portaria/feriasview.html', {'qs': qs, 'dias': dias, 'hoje': hoje})
            elif opt == 'Próximas do vencimento':
                qs = feriaspj.objects.filter(quitado=False, funcionario_id__in=aa, vencimento__gte= hoje,vencimento__lte=dias).order_by('vencimento')
                return render(request, 'portaria/feriasview.html', {'qs': qs, 'dias': dias, 'hoje': hoje})
            else:
                pass
        elif opt == '' and name:
            qs = feriaspj.objects.filter(quitado=False, funcionario_id__in=aa, funcionario__nome__contains=name).order_by('vencimento')
            return render(request, 'portaria/feriasview.html', {'qs': qs, 'dias': dias, 'hoje': hoje})
        elif name and opt:
            if opt == 'Férias Vencidas':
                qs = feriaspj.objects.filter(quitado=False, funcionario_id__in=aa, vencimento__lte = hoje, funcionario__nome__contains=name).order_by('vencimento')
                return render(request, 'portaria/feriasview.html', {'qs': qs,'dias':dias,'hoje':hoje})
            elif opt == 'Próximas do vencimento':
                qs = feriaspj.objects.filter(quitado=False, funcionario_id__in=aa, vencimento__gte= hoje,vencimento__lte=dias, funcionario__nome__contains=name).order_by('vencimento')
                return render(request, 'portaria/feriasview.html', {'qs': qs,'dias':dias,'hoje':hoje})
            return render(request, 'portaria/feriasview.html', {'qs': qs, 'dias': dias, 'hoje': hoje})


    return render(request, 'portaria/feriasview.html', {'qs': qs,'dias':dias,'hoje':hoje})

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
            return render(request, 'portaria/agendamento.html', {'fer':fer})
        else:
            messages.success(request, 'Agendamento feito com sucesso')
            return redirect('portaria:feriasview')
    return render(request, 'portaria/agendamento.html', {'fer':fer,'form':form})

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
    return render(request, 'portaria/frotacadastros.html')

def cadmotorista(request):
    form = MotoristaForm
    if request.method == 'POST':
        form = MotoristaForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastrado com sucesso')
            return redirect('portaria:frotacadastros')
    return render(request, 'portaria/cadmotorista.html', {'form':form})

def cadveiculo(request):
    form = VeiculosForm
    if request.method == 'POST':
        form = VeiculosForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastrado com sucesso')
            return redirect('portaria:frotacadastros')
    return render(request, 'portaria/cadveiculo.html', {'form': form})

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
            return render(request, 'portaria/manutencaofrota.html')
        else:
            return redirect('portaria:manusaida', osid=idmanu)
    return render(request, 'portaria/manutencaofrota.html')

@login_required
def manuentrada(request, placa_id):
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
            manu.save()
            ServJoinManu.objects.create(id_svs=tp_sv,autor=autor,id_os_id=manu.id)
            if count:
                ncount = int(count)
                if ncount > 0:
                    for c in range(0, ncount):
                        d = c + 1
                        variable = 'tp_servico' + str(d)
                        tp_sv = request.POST.get(variable)
                        if tp_sv:
                            ServJoinManu.objects.create(id_svs=tp_sv,autor=autor,id_os_id=manu.id)
                        else:
                            continue
            messages.success(request, f'Cadastro de manutenção do veículo {placa} feito com sucesso!')
            return redirect('portaria:manutencaoprint', osid= manu.id)
    return render(request, 'portaria/manuentrada.html', {'placa':placa,'form':form})

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
    return render(request,'portaria/manutencaopendencia.html', {'qs':qs,'qs2':qs2})


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
                return render(request, 'portaria/manusaida.html',{'get_os':get_os})
            else:
                between_days = (date_dtsaida - get_os.dt_entrada).days
                ManutencaoFrota.objects.filter(pk=get_os.id).update(valor_peca=vlpeca,valor_maodeobra=vlmao,
                                                                    dt_saida=date_dtsaida,
                                                                    dias_veic_parado=str(between_days),
                                                                    status='PENDENTE',
                                                                    autor=request.user)

                messages.success(request, f'Saída cadastrada para OS {get_os.id}, placa {get_os.veiculo}')
                return redirect('portaria:manutencaoview')
        return render(request, 'portaria/manusaida.html',{'get_os':get_os})
    else:
        messages.error(request, 'Saída já cadastrada para OS')
        return redirect('portaria:manutencaofrota')

class ManutencaoListView(generic.ListView):
    template_name = 'portaria/manutencaoview.html'
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
    aa = ServJoinManu.objects.filter(id_os=os.id).values_list('id_svs', flat=True)
    return render(request, 'portaria/manutencaoprint.html', {'os':os,'aa':aa})

def fatferramentas(request):
    return render(request,'portaria/fatferramentas.html')

def monitticket(request):
    form = EmailMonitoramento.objects.all()
    return render(request, 'portaria/monitticket.html', {'form':form})

def tktcreate(request):
    if request.method == 'POST':
        responsavel = request.user
        cc = request.POST.get('cc')
        cliente = request.POST.get('cliente')
        assunto = request.POST.get('assunto')
        mensagem = request.POST.get('msg')
        if responsavel and cc and cliente and assunto and mensagem:
            #return redirect('portaria:createtktandmail', resp=responsavel,cc=cc,cli=cliente,assunto=assunto,msg=mensagem)
            createtktandmail(request,resp=responsavel,cc=cc,cli=cliente,assunto=assunto,msg=mensagem)
        else:
            messages.error(request, 'Está faltando campos')
            return redirect('portaria:tktcreate')
    return render(request, 'portaria/tktcreate.html')

#fim das views


#funcoes variadas
@login_required
def transfpalete(request):
    context = {}
    form = TPaletesForm()
    context['form'] = form
    if request.method == 'POST':
        ori = request.POST.get('origem_')
        des = request.POST.get('destino_')
        qnt = int(request.POST.get('quantidade_'))
        plc = request.POST.get('placa_veic')
        if qnt <= PaleteControl.objects.filter(loc_atual=ori).count():
            for x in range(qnt):
                q = PaleteControl.objects.filter(loc_atual=ori).first()
                PaleteControl.objects.filter(pk=q.id).update(origem=ori,destino=des, loc_atual=des,
                                                             placa_veic=plc,ultima_viagem=timezone.now(), autor=request.user)

            messages.success(request, f'{qnt} palete transferido de {ori} para {des}')
            return render(request,'portaria/transfpaletes.html', {'form':form})
        else:
            messages.error(request,'Quantidade solicitada maior que a disponível')
            return render(request,'portaria/transfpaletes.html', {'form':form})

    return render(request,'portaria/transfpaletes.html', context)

@login_required
def get_nfpj_mail(request):
    data1 = request.POST.get('dataIni')
    data2 = request.POST.get('dataFim')
    dateparse = datetime.datetime.strptime(data1, '%Y-%m-%d').replace(hour=00, minute=00)
    dateparse1 = datetime.datetime.strptime(data2, '%Y-%m-%d').replace(hour=23, minute=59)
    arrya = []
    qs = FuncPj.objects.filter(ativo=True)
    for q in qs:
        query = FuncPj.objects.filter(pk=q.id) \
            .annotate(
             faculdade=Coalesce(Sum('nfservicopj__faculdade',filter=Q(nfservicopj__data_emissao__lte=dateparse1, nfservicopj__data_emissao__gte=dateparse)), Value(0.0)),
             cred_convenio=Coalesce(Sum('nfservicopj__cred_convenio', filter=Q(nfservicopj__data_emissao__lte=dateparse1,nfservicopj__data_emissao__gte=dateparse)), Value(0.0)),
             outros_cred=Coalesce(Sum('nfservicopj__outros_cred', filter=Q(nfservicopj__data_emissao__lte=dateparse1,nfservicopj__data_emissao__gte=dateparse)), Value(0.0)),
             desc_convenio=Coalesce(Sum('nfservicopj__desc_convenio', filter=Q(nfservicopj__data_emissao__lte=dateparse1,nfservicopj__data_emissao__gte=dateparse)), Value(0.0)),
             outros_desc=Coalesce(Sum('nfservicopj__outros_desc',filter=Q(nfservicopj__data_emissao__lte=dateparse1, nfservicopj__data_emissao__gte=dateparse)), Value(0.0)),
             ).annotate(total=(F('salario') + F('ajuda_custo') + F('faculdade') + F('cred_convenio') + F('outros_cred') ) - (F('adiantamento') + F('desc_convenio') + F('outros_desc')))
        arrya.extend(query)
    for q in arrya:
        send_mail(
            subject='Teste',
            message=f'''
                        Unidade: {q.filial}
                        Nome: {q.nome}
                        Salario: {q.salario:.2f}
                        Faculdade: {q.faculdade:.2f}
                        Ajuda de Custo: {q.ajuda_custo:.2f}
                        Creditos Convenio: {q.cred_convenio:.2f}
                        Outros Creditos: {q.outros_cred:.2f}
                        Adiantamento: {q.adiantamento:.2f}
                        Descontos Convenio: {q.desc_convenio:.2f}
                        Outros Descontos: {q.outros_desc:.2f}
                        Total pagamento: {q.total:.2f}
                        Cpf/Cnpj: {q.cpf_cnpj}
                        Dados bancários: {q.banco} / {q.ag} / {q.conta} / {q.op}
                                ''',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[q.email]
        )
    return redirect('portaria:index')

def get_pj13_mail(request):
    getperiod = request.POST.get('period')
    array = []
    print(getperiod)
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
                            headers={'Content-Disposition': 'attachment; filename="paletes.csv"'})
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
    print(fil, data1, data2)
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
    writer = csv.writer(response)
    writer.writerow(['id','loc_atual','ultima_viagem','origem','destino','placa_veic','autor'])
    palete = PaleteControl.objects.all().values_list(
        'id', 'loc_atual', 'ultima_viagem', 'origem', 'destino', 'placa_veic','autor_username'
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
        manutencao = ManutencaoFrota.objects.all().values_list('id','veiculo','tp_manutencao','local_manu','dt_ult_manutencao','dt_entrada','dt_saida',
                            'dias_veic_parado','km_ult_troca_oleo','tp_servico','valor_maodeobra','valor_peca',
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
            faculdade=Coalesce(Sum('nfservicopj__faculdade', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month)),Value(0.0)),
            cred_convenio=Coalesce(Sum('nfservicopj__cred_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month)), Value(0.0)),
            outros_cred=Coalesce(Sum('nfservicopj__outros_cred', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month)), Value(0.0)),
            desc_convenio=Coalesce(Sum('nfservicopj__desc_convenio', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month)), Value(0.0)),
            outros_desc=Coalesce(Sum('nfservicopj__outros_desc', filter=Q(nfservicopj__data_emissao__month=datetime.datetime.now().month)), Value(0.0)),) \
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
                                                            'p3_2','p3_3','p3_4','p3_5','p3_6','p3_7','p3_8','autor__username').filter(datachecklist__gte=ini,datachecklist__lte=fim)
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
    host = 'pop.kinghost.net'
    e_user = 'bora@bora.tec.br'
    e_pass = 'Bor@dev#123'

    pp = poplib.POP3(host)
    pp.set_debuglevel(1)
    pp.user(e_user)
    pp.pass_(e_pass)

    num_messages = len(pp.list()[1])
    for i in range(num_messages):
        try:
            raw_email = b'\n'.join(pp.retr(i+1)[1])
            parsed_email = email.message_from_bytes(raw_email, policy=policy.compat32)
        except Exception as e:
            print(f'parsed -- ErrorType: {type(e).__name__}, Error: {e}')
        else:
            if parsed_email.is_multipart():
                for part in parsed_email.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get('Content-Disposition'))
                    if ctype == 'text/plain' and 'attatchment' not in cdispo:
                        body = part.get_payload(decode=True)
            else:
                body = parsed_email.get_payload(decode=True)
            cs = parsed_email.get_charsets()
            for q in cs:
                if q is None: continue
                else: cs = q
            try:
                e_title = parsed_email['Subject']
                e_from = parsed_email['From']
                e_to = parsed_email['To']
                e_cc = parsed_email['CC']
                e_id = parsed_email['Message-ID']
                e_ref = parsed_email['References']
                e_body = body.decode(cs)
                if e_ref is not None: e_ref = e_ref.split(' ')[0]
            except Exception as e:
                print(f'insert data -- ErrorType: {type(e).__name__}, Error: {e}')
            else:
                form = EmailMonitoramento.objects.all()
                if form.filter(email_id=e_ref).exists():
                    form.filter(email_id=e_ref).update(ult_resp=e_body,ult_rest_dt=timezone.now())
                pp.dele(i+1)
    pp.quit()
    return redirect('portaria:monitticket')

def createtktandmail(request,resp,cc,cli,assunto,msg):
    print('entrou na funcao')
    msg1 = MIMEText(msg, 'html', 'utf-8')
    print('carregou mimetext')
    msg1['Subject'] = assunto
    msg1['From'] = 'bora@bora.tec.br'
    msg1['To'] = cli
    msg1['CC'] = cc
    msg_id = make_msgid(idstring=None, domain='bora.tec.br')
    msg1['Message-ID'] = msg_id
    smtp_h = 'smtp.kinghost.net'
    smtp_p = '587'
    user = 'bora@bora.tec.br'
    passw = 'Bor@dev#123'
    print('setou parametros iniciando trycatch')
    try:
        print('entrou no try')
        sm = smtplib.SMTP(smtp_h, smtp_p)
        sm.set_debuglevel(1)
        sm.login(user,passw)
        sm.sendmail('bora@bora.tec.br', cli, msg1.as_string())
        print('mandou o email')
    except Exception as e:
        print(f'ErrorType:{type(e).__name__}, Error:{e}')
    else:
        print('entrou no else')
        tkt = TicketMonitoramento.objects.create(nome_tkt=assunto, dt_abertura=timezone.now(), responsavel=request.user,cliente=cli)
        EmailMonitoramento.objects.create(assunto=assunto, mensagem=msg, cc=cc,dt_envio=timezone.now(),email_id=msg_id,tkt_ref_id=tkt.id)
        print('criou os objetos no banco')
        messages.success(request, 'Email enviado e ticket criado com sucesso')
        return redirect('portaria:monitticket')
