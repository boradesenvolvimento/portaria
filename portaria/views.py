import csv
import datetime


from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import Count, Sum, F, Q, Case, When, Value, IntegerField
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
                order = form.save(commit=False)
                order.placa = uplaca
                order.autor = autor
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
        return render(request, 'portaria/cadastro.html')
    else:
        auth_message = 'Usuário não autenticado, por favor logue novamente'
        return render(request, 'portaria/cadastro.html', {'auth_message': auth_message})

@login_required
def outputs(request):
    return render(request, 'portaria/outputs.html')


class PaletView(generic.ListView):
    paginate_by = 10
    template_name = 'portaria/palets.html'
    context_object_name = 'lista'

    def get_queryset(self):
        qs = PaletControl.objects.values("loc_atual").annotate(num_ratings=Count("id"))
        return qs

def frota(request):
    context = {}
    form = FilterForm()
    context['form'] = form
    if request.method == "GET":
        foo = request.GET.get('filter_')
        if foo:
            try:
                bar = Veiculos.objects.get(prefixoveic=foo)
            except ObjectDoesNotExist:
                return render(request, 'portaria/frota.html',
                              {'form': form, 'error_message': 'Cadastro não encontrado'})
            else:
                return redirect('portaria:checklistfrota',placa_id = bar)
    return render(request, 'portaria/frota.html', context)

@login_required
def checklistfrota(request, placa_id):
    test = get_object_or_404(Veiculos, prefixoveic = placa_id)
    context = {}
    form = ChecklistForm
    context['form'] = form
    if request.method == 'POST':
        form = ChecklistForm(request.POST)
        if form.is_valid():
            obar = form.save(commit=False)
            obar.placaveic = test
            obar.motoristaveic = test.codmotorista
            obar.save()
            return HttpResponseRedirect(reverse('portaria:frota'), {'success_message': 'success_message'})
    return render(request,'portaria/checklistfrota.html', {'form':form,'test':test})

def servicospj(request):
    func = request.GET.get('nomefunc')
    array = []
    qnt_funcs = FuncPj.objects.filter(ativo=True)
    for q in qnt_funcs:
        query = FuncPj.objects.filter(pk=q.id)
        array.extend(query)
    if func:
        cad = FuncPj.objects.all().filter(nome__icontains=func)
        if cad:
            array.clear()
            for c in cad:
                query = FuncPj.objects.filter(pk=c.id)
                array.extend(query)
    return render(request, 'portaria/servicospj.html', {'array': array})

def consultanfpj(request):
    arrya = []
    qnt_funcs = FuncPj.objects.filter(ativo=True)
    for q in qnt_funcs:
        query = FuncPj.objects.filter(pk=q.id, nfservicopj__data_emissao__month=datetime.datetime.now().month) \
            .annotate(premios=Sum('nfservicopj__premios_faculdade'),
                      ajuda_custo=Sum('nfservicopj__ajuda_custo'),
                      adiantamento=Sum('nfservicopj__adiantamento'),
                      convenio=Sum('nfservicopj__convenio'),
                      outros=Sum('nfservicopj__outros_desc'), ) \
            .annotate(total=F('salario') + F('premios') + F('ajuda_custo') - (F('adiantamento') + F('convenio') + F('outros')))
        arrya.extend(query)
    return render(request, 'portaria/consultanfpj.html', {'arrya': arrya})

def cadservicospj(request, args):
    form = ServicoPjForm(request.POST or None)
    func = get_object_or_404(FuncPj, pk=args)
    if request.method == 'POST':
        if form.is_valid():
            calc = form.save(commit=False)
            calc.funcionario = func
            calc.save()
            messages.success(request, f'Valores cadastrados com sucesso para {calc.funcionario}')
            return HttpResponseRedirect(reverse('portaria:servicospj'))

    return render(request, 'portaria/cadservicospj.html', {'form':form,'func':func})


#fim das views


#funcoes variadas
@login_required
def transfpalet(request):
    context = {}
    form = TPaletsForm()
    context['form'] = form
    if request.method == 'POST':
        ori = request.POST.get('origem_')
        des = request.POST.get('destino_')
        qnt = int(request.POST.get('quantidade_'))
        plc = request.POST.get('placa_veic')
        if qnt <= PaletControl.objects.filter(loc_atual=ori).count():
            for x in range(qnt):
                q = PaletControl.objects.filter(loc_atual=ori).first()
                PaletControl.objects.filter(pk=q.id).update(origem=ori,destino=des, loc_atual=des, placa_veic=plc,ultima_viagem=timezone.now())

            messages.success(request, f'{qnt} palet transferido de {ori} para {des}')
            return render(request,'portaria/transfpalets.html', {'form':form})
        else:
            messages.error(request,'Quantidade solicitada maior que a disponível')
            return render(request,'portaria/transfpalets.html', {'form':form})

    return render(request,'portaria/transfpalets.html', context)

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
             premios=Coalesce(Sum('nfservicopj__premios_faculdade',filter=Q(nfservicopj__data_emissao__lte=dateparse1, nfservicopj__data_emissao__gte=dateparse)), Value(0)),
             ajuda_custo=Coalesce(Sum('nfservicopj__ajuda_custo', filter=Q(nfservicopj__data_emissao__lte=dateparse1,nfservicopj__data_emissao__gte=dateparse)), Value(0)),
             adiantamento=Coalesce(Sum('nfservicopj__adiantamento', filter=Q(nfservicopj__data_emissao__lte=dateparse1,nfservicopj__data_emissao__gte=dateparse)), Value(0)),
             convenio=Coalesce(Sum('nfservicopj__convenio', filter=Q(nfservicopj__data_emissao__lte=dateparse1,nfservicopj__data_emissao__gte=dateparse)), Value(0)),
             outros=Coalesce(Sum('nfservicopj__outros_desc',filter=Q(nfservicopj__data_emissao__lte=dateparse1, nfservicopj__data_emissao__gte=dateparse)), Value(0)),
             ).annotate(total=F('salario') + F('premios') + F('ajuda_custo') - (F('adiantamento') + F('convenio') + F('outros')))
        arrya.extend(query)
    for q in arrya:
        fil = q.filial
        nome = q.nome
        sal = q.salario
        premio = q.premios
        ajuda = q.ajuda_custo
        adian = q.adiantamento
        conv = q.convenio
        outr = q.outros
        cpf = q.cpf
        cnpj = q.cnpj
        bco = q.banco
        ag = q.ag
        conta = q.conta
        op = q.op
        toemail = q.email
        total = q.total
        print(q.premios,q.total)
        send_mail(
            subject='Teste',
            message=f'''
                        Unidade: {fil}
                        Nome: {nome}
                        Salario: {sal}
                        Premio / Faculdade: {premio}
                        Ajuda de Custo: {ajuda}
                        Adiantamento: {adian}
                        Convenio: {conv}
                        Outros Descontos: {outr}
                        Total pagamento: {total}
                        Cpf/Cnpj: {cpf} - {cnpj}
                        Dados bancários: {bco} / {ag} / {conta} / {op}
                                ''',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[toemail]
        )
    return redirect('portaria:index')

def get_portaria_csv(request):
    data1 = request.POST.get('dataIni')
    data2 = request.POST.get('dataFim')
    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition': 'attachment; filename="portaria.csv"'},
                            )
    dateparse = datetime.datetime.strptime(data1, '%d/%m/%Y').replace(hour=23, minute=59)
    dateparse1 = datetime.datetime.strptime(data2, '%d/%m/%Y').replace(hour=23, minute=59)
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(['Placa','Placa2','Motorista','Empresa','Origem','Destino','Tipo_mot','Tipo_viagem','Hr_entrada','Hr_Saida','autor'])
    cadastro = Cadastro.objects.all().values_list(
                        'placa', 'placa2', 'motorista', 'empresa', 'origem','destino',
                            'tipo_mot', 'tipo_viagem', 'hr_chegada', 'hr_saida', 'autor').filter(hr_chegada__gte=dateparse,hr_chegada__lte=dateparse1)
    for placa in cadastro:
        writer.writerow(placa)
    return response

def get_palet_csv(request):
    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition':'attachment; filename="palets.csv"'})
    writer = csv.writer(response)
    writer.writerow(['id','loc_atual','ultima_viagem','origem','destino','placa_veic'])
    palet = PaletControl.objects.all().values_list(
        'id', 'loc_atual', 'ultima_viagem', 'origem', 'destino', 'placa_veic'
    )
    for id in palet:
        writer.writerow(id)
    return response



