import csv
import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from .models import Cadastro, PaletControl
from .forms import CadastroForm, isPlacaForm, DateForm, FilterForm, TPaletsForm


#views
@login_required
def index(request):
    return render(request, 'portaria/index.html')


class Visualizacao(generic.ListView):
    paginate_by = 10
    template_name = 'portaria/visualizacao.html'
    context_object_name = 'lista'
    form = DateForm()

    def get_queryset(self):
        form_input1 = self.request.GET.get('date')
        form_input2 = self.request.GET.get('date1')

        qs = Cadastro.objects.all().filter(hr_chegada__month=datetime.datetime.now().month).order_by('-hr_chegada')
        if form_input1 and form_input2:
            self.dateparse1 = datetime.datetime.strptime(form_input1, '%d/%m/%Y').replace(hour=23, minute=59)
            self.dateparse2 = datetime.datetime.strptime(form_input2, '%d/%m/%Y').replace(hour=23, minute=59)
            qs = Cadastro.objects.all().filter(hr_chegada__gte=self.dateparse1,hr_chegada__lte=self.dateparse2).order_by('-hr_chegada')
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
                order = form.save(commit=False)
                order.autor = autor
                order.save()
                return redirect('portaria:index')
        return render(request, 'portaria/cadastroentrada.html', {'cadastro':cadastro,'form':form})
    else:
        auth_message = 'Usuário não autenticado, por favor logue novamente'
        return render(request, 'portaria/cadastroentrada.html', {'auth_message': auth_message})

@login_required
def cadastrosaida(request, placa_id):
    five_days_back = timezone.now() - datetime.timedelta(days=5)
    loc_placa = Cadastro.objects.filter(placa=placa_id, hr_chegada__lte=timezone.now(), hr_chegada__gte=five_days_back,
                                        hr_saida=None).order_by('-hr_chegada').first()
    try:
        Cadastro.objects.get(pk=loc_placa.id)
    except AttributeError:
        return render(request,'portaria/cadastrosaida.html', {'error_message': 'Não encontrado'})
    else:
        Cadastro.objects.filter(pk=loc_placa.id).update(hr_saida=timezone.now(), autor=request.user)
        return HttpResponseRedirect(reverse('portaria:cadastro'), {'success_message':'success_message'})

@login_required
def cadastro(request):
    if request.user.is_authenticated:
        form_class = isPlacaForm
        form = form_class(request.POST or None)
        if request.method == 'POST':
            form = isPlacaForm(request.POST)
            if form.is_valid():
                s_query = form.cleaned_data['search_placa']
                return redirect('portaria:cadastrosaida', placa_id=s_query)
        return render(request, 'portaria/cadastro.html', {'form': form})
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
        qs = PaletControl.objects.all()
        self.form_input = self.request.GET.get('filter_')
        if self.form_input:
            qs = PaletControl.objects.filter(loc_atual=self.form_input)
        return qs

    def get_context_data(self, **kwargs):
        context = super(PaletView, self).get_context_data(**kwargs)
        context['form'] = FilterForm()
        return context

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
        print(qnt)
        if qnt <= PaletControl.objects.filter(loc_atual=ori).count():
            for x in range(qnt):
                q = PaletControl.objects.filter(loc_atual=ori).first()
                PaletControl.objects.filter(pk=q.id).update(origem=ori,destino=des, loc_atual=des, placa_veic=plc,ultima_viagem=timezone.now())

            success_message = f'{qnt} palets transferidos de {ori} para {des}'
            return render(request,'portaria/transfpalets.html', {'form':form,'success_message': success_message})
        else:
            error_message = 'Quantidade solicitada maior que a disponível'
            return render(request,'portaria/transfpalets.html', {'form':form,'error_message':error_message})

    return render(request,'portaria/transfpalets.html', context)

def get_portaria_csv(request):
    data1 = request.POST.get('dataIni')
    data2 = request.POST.get('dataFim')
    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition': 'attachment; filename="portaria.csv"'},
                            )
    dateparse = datetime.datetime.strptime(data1, '%d/%m/%Y').replace(hour=23, minute=59)
    dateparse1 = datetime.datetime.strptime(data2, '%d/%m/%Y').replace(hour=23, minute=59)
    writer = csv.writer(response)
    writer.writerow(['Placa','Placa2','Motorista','Empresa','Garagem','Tipo_mot','Tipo_viagem','Hr_entrada','Hr_Saida','autor'])
    cadastro = Cadastro.objects.all().values_list(
                        'placa', 'placa2', 'motorista', 'empresa', 'garagem',
                            'tipo_mot', 'tipo_viagem', 'hr_chegada', 'hr_saida', 'autor').filter(hr_chegada__gte=dateparse,hr_chegada__lte=dateparse1)
    for placa in cadastro:
        writer.writerow(placa)
    return response



