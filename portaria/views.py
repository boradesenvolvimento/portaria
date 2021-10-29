import csv
import datetime


from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import Count, Sum, F, Q, Value, FloatField, DecimalField
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.template.defaultfilters import upper
from django.urls import reverse
from django.utils import timezone
from django.views import generic


from .models import * #Cadastro, PaletControl, ChecklistFrota, Veiculos, NfServicoPj
from .forms import * #CadastroForm, isPlacaForm, DateForm, FilterForm, TPaletsForm, TIPO_GARAGEM, ChecklistForm

def telausuariothiago(request):
    return render(request, "portaria/telausuariothiago.html")

def telausuariorodrigo(request):
    return render(request, "portaria/telausuariorodrigo.html")

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
        qs = Cadastro.objects.all().filter(hr_chegada__month=datetime.datetime.now().month).order_by('-hr_chegada')
        try:
            form_input1 = self.request.GET.get('date')
            form_input2 = self.request.GET.get('date1')
            if form_input1 and form_input2:
                self.dateparse1 = datetime.datetime.strptime(form_input1, '%d/%m/%Y').replace(hour=00, minute=00)
                self.dateparse2 = datetime.datetime.strptime(form_input2, '%d/%m/%Y').replace(hour=23, minute=59)
                qs = Cadastro.objects.all().filter(hr_chegada__gte=self.dateparse1,
                                                   hr_chegada__lte=self.dateparse2).order_by('-hr_chegada')
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
                new_date_str = datetime.datetime.strftime(timezone.now(), settings.DATETIME_FORMAT)
                new_date_date = datetime.datetime.strptime(new_date_str, settings.DATETIME_FORMAT)
                order = form.save(commit=False)
                order.placa = uplaca
                order.autor = autor
                order.hr_chegada = new_date_date
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
                #five_days_back = timezone.now() - datetime.timedelta(days=5)
                loc_placa = Cadastro.objects.filter(placa=s_query, hr_chegada__month=datetime.datetime.now().month,
                                                    hr_saida=None).order_by('-hr_chegada').first()
                try:
                    Cadastro.objects.get(pk=loc_placa.id)
                except AttributeError:
                    messages.error(request, 'Não encontrado')
                    return render(request, 'portaria/cadastrosaida.html', {'form':form})
                else:
                    new_date_str = datetime.datetime.strftime(timezone.now(), settings.DATETIME_FORMAT)
                    new_date_date = datetime.datetime.strptime(new_date_str, settings.DATETIME_FORMAT)
                    Cadastro.objects.filter(pk=loc_placa.id).update(hr_saida=new_date_date, destino=q_query, autor=request.user)
                    messages.success(request, 'Saida cadastrada com sucesso.')
                    return HttpResponseRedirect(reverse('portaria:cadastro'))
        return render(request, 'portaria/cadastrosaida.html', {'form':form})
    else:
        auth_message = 'Usuário não autenticado, por favor logue novamente'
        return render(request, 'portaria/cadastrosaida.html', {'auth_message': auth_message})

@login_required
def cadastro(request):
    if request.user.is_authenticated:
        return render(request, 'portaria/cadastro.html')
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
    return render(request, 'portaria/frota.html')

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
            return HttpResponseRedirect(reverse('portaria:frota'), {'success_message': 'success_message'})
    return render(request,'portaria/checklistfrota.html', {'form':form,'pla':pla, 'mot':mot})

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
        else:
            return redirect('portaria:manusaida', osid=idmanu)
    return render(request, 'portaria/manutencaofrota.html')

@login_required
def manuentrada(request, placa_id):
    placa = get_object_or_404(Veiculos, prefixoveic=placa_id)
    form = ManutencaoForm
    autor = request.user
    ult_manu = Veiculos.objects.filter(pk=placa.codigoveic).values_list('manutencaofrota__dt_saida', flat=True).order_by('-manutencaofrota__dt_saida').first()
    if ult_manu == None: ult_manu = timezone.now()
    if request.method == 'POST':
        form = ManutencaoForm(request.POST or None)
        if form.is_valid():
            manu = form.save(commit=False)
            manu.veiculo_id = placa.codigoveic
            manu.dt_ult_manutencao = ult_manu
            manu.dt_entrada = timezone.now()
            manu.status = 'ANDAMENTO'
            manu.autor = autor
            manu.save()
            messages.success(request, f'Cadastro de manutenção do veículo {placa} feito com sucesso!')
            return redirect('portaria:manutencaoprint', osid= manu.id)
    return render(request, 'portaria/manuentrada.html', {'placa':placa,'form':form})

def manupendentes(request):
    qs = ManutencaoFrota.objects.filter(status='PENDENTE').order_by('dt_entrada')

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
    return render(request,'portaria/manutencaopendencia.html', {'qs':qs})


@login_required
def manusaida(request, osid):
    get_os = get_object_or_404(ManutencaoFrota, pk=osid)
    if get_os.dt_saida == None:
        dtsaida = request.POST.get('dtsaida')
        vlmao = request.POST.get('vlmao')
        vlpeca = request.POST.get('vlpeca')
        if dtsaida and vlpeca and vlmao:
            date_dtsaida = datetime.datetime.strptime(dtsaida, '%d/%m/%Y').date()
            between_days = (date_dtsaida - get_os.dt_entrada).days
            ManutencaoFrota.objects.filter(pk=get_os.id).update(valor_peca=vlpeca,valor_maodeobra=vlmao,
                                                                dt_saida=date_dtsaida,
                                                                dias_veic_parado=str(between_days),
                                                                status='PENDENTE',
                                                                autor=request.user)

            messages.success(request, f'Saída cadastrada para OS {get_os.id}, placa {get_os.veiculo}')
            return redirect('portaria:manutencaofrota')
        return render(request, 'portaria/manusaida.html',{'get_os':get_os})
    else:
        messages.error(request, 'Saída já cadastrada para OS')
        return redirect('portaria:manutencaofrota')

class ManutencaoListView(generic.ListView):
    template_name = 'portaria/manutencaoview.html'
    context_object_name = 'lista'

    def get_queryset(self):
        qs = ManutencaoFrota.objects.filter(dt_saida=None).order_by('dt_entrada')
        try:
            placa = self.request.GET.get('isplaca')
            if placa:
                qs = ManutencaoFrota.objects.filter(dt_saida=None, veiculo__prefixoveic=placa).order_by('dt_entrada')
        except ObjectDoesNotExist:
            raise Exception('Valor digitado inválido')
        return qs

@login_required
def manutencaoprint(request, osid):
    os = get_object_or_404(ManutencaoFrota, pk=osid)
    return render(request, 'portaria/manutencaoprint.html', {'os':os})

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
                PaleteControl.objects.filter(pk=q.id).update(origem=ori,destino=des, loc_atual=des, placa_veic=plc,ultima_viagem=timezone.now(), autor=request.user)

            messages.success(request, f'{qnt} palete transferido de {ori} para {des}')
            return render(request,'portaria/transfpaletes.html', {'form':form})
        else:
            messages.error(request,'Quantidade solicitada maior que a disponível')
            return render(request,'portaria/transfpaletes.html', {'form':form})

    return render(request,'portaria/transfpaletes.html', context)

@login_required
def get_nfpj_csv(request):
    data1 = request.POST.get('dataIni')
    data2 = request.POST.get('dataFim')
    dateparse = datetime.datetime.strptime(data1, '%d/%m/%Y').replace(hour=00, minute=00)
    dateparse1 = datetime.datetime.strptime(data2, '%d/%m/%Y').replace(hour=23, minute=59)
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

def get_portaria_csv(request):
    data1 = request.POST.get('dataIni')
    data2 = request.POST.get('dataFim')
    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition': 'attachment; filename="portaria.csv"'},
                            )
    dateparse = datetime.datetime.strptime(data1, '%d/%m/%Y').replace(hour=00, minute=00)
    dateparse1 = datetime.datetime.strptime(data2, '%d/%m/%Y').replace(hour=23, minute=59)
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(['Placa','Placa2','Motorista','Empresa','Origem','Destino','Tipo_mot','Tipo_viagem','Hr_entrada','Hr_Saida','autor'])
    cadastro = Cadastro.objects.all().values_list(
                        'placa', 'placa2', 'motorista', 'empresa', 'origem','destino',
                            'tipo_mot', 'tipo_viagem', 'hr_chegada', 'hr_saida', 'autor').filter(hr_chegada__gte=dateparse,hr_chegada__lte=dateparse1)
    for placa in cadastro:
        writer.writerow(placa)
        print(placa)
    return response

def get_palete_csv(request):
    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition':'attachment; filename="paletes.csv"'})
    writer = csv.writer(response)
    writer.writerow(['id','loc_atual','ultima_viagem','origem','destino','placa_veic','autor'])
    palete = PaleteControl.objects.all().values_list(
        'id', 'loc_atual', 'ultima_viagem', 'origem', 'destino', 'placa_veic','autor'
    )
    for id in palete:
        writer.writerow(id)
    return response

def get_manu_csv(request):
    data1 = request.POST.get('dataIni')
    data2 = request.POST.get('dataFin')
    dateparse = datetime.datetime.strptime(data1, '%d/%m/%Y')
    dateparse1 = datetime.datetime.strptime(data2, '%d/%m/%Y')
    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition':f'attatchment; filename="manutencao{dateparse}-{dateparse1}.csv"'})
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(['id','veiculo','tp_manutencao','local_manu','dt_ult_manutencao','dt_entrada','dt_saida',
                        'dias_veic_parado','km_ult_troca_oleo','tp_servico','valor_maodeobra','valor_peca',
                            'filial','socorro','prev_entrega','observacao','status','autor'])
    manutencao = ManutencaoFrota.objects.all().values_list('id','veiculo','tp_manutencao','local_manu','dt_ult_manutencao','dt_entrada','dt_saida',
                        'dias_veic_parado','km_ult_troca_oleo','tp_servico','valor_maodeobra','valor_peca',
                            'filial','socorro','prev_entrega','observacao','status','autor').filter(dt_entrada__gte=dateparse, dt_entrada__lte=dateparse1)
    for id in manutencao:
        writer.writerow(id)
    return response



