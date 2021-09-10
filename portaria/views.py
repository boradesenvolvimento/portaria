import csv
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views import generic
from .models import Cadastro
from .forms import CadastroForm, isPlacaForm

#views

def index(request):
    return render(request, 'portaria/index.html')

class Visualizacao(generic.ListView):
    template_name = 'portaria/visualizacao.html'
    context_object_name = 'lista'

    def get_queryset(self):
        return Cadastro.objects.all()

def cadastroentrada(request, cadastro_id):
    if request.user.is_authenticated:
        cadastro = get_object_or_404(Cadastro, pk=cadastro_id)
        form = CadastroForm(request.POST or None, instance=cadastro)
        if request.method == 'POST':
            if form.is_valid():
                fil = form.cleaned_data['filial']
                ga = form.cleaned_data['filial']
                timer = str(timezone.now())
                Cadastro.objects.filter(pk=cadastro).update(filial=fil, garagem=ga, hr_chegada=timer, hr_saida=None, autor=request.user)
                return redirect('portaria:index')
        return render(request, 'portaria/cadastroentrada.html', {'cadastro':cadastro,'form':form})
    else:
        auth_message = 'Usuário não autenticado, por favor logue novamente'
        return render(request, 'portaria/cadastrosaida.html', {'auth_message': auth_message})

def cadastrosaida(request, cadastro_id):
    if request.user.is_authenticated:
        cadastro = get_object_or_404(Cadastro, pk=cadastro_id)
        form = CadastroForm(request.POST or None, instance=cadastro)
        if request.method == 'POST':
            if form.is_valid():
                fil = form.cleaned_data['filial']
                ga = form.cleaned_data['filial']
                timer = str(timezone.now())
                Cadastro.objects.filter(pk=cadastro).update(filial=fil, garagem=ga, hr_saida=timer, autor=request.user)
                return redirect('portaria:index')
        return render(request, 'portaria/cadastrosaida.html', {'form': form, 'cadastro': cadastro})
    else:
        auth_message = 'Usuário não autenticado, por favor logue novamente'
        return render(request, 'portaria/cadastrosaida.html', {'auth_message':auth_message})

def cadastro(request):
    if request.user.is_authenticated:
        form_class = isPlacaForm
        form = form_class(request.POST or None)
        if request.method == 'POST':
            form = isPlacaForm(request.POST)
            if form.is_valid():
                s_query = form.cleaned_data['search_placa']
                j_query = form.cleaned_data['tipo_veic']
                try:
                    Cadastro.objects.get(pk=s_query)
                except Cadastro.DoesNotExist:
                    return render(request, 'portaria/cadastro.html', {'form': form, 'error_message': 'Não encontrado!'})
                else:
                    if j_query == '1':
                        return redirect('portaria:cadastroentrada', cadastro_id=request.POST['search_placa'])
                    elif j_query == '2':
                        return redirect('portaria:cadastrosaida', cadastro_id=request.POST['search_placa'])
        else:
            form = isPlacaForm()
        return render(request, 'portaria/cadastro.html', {'form': form})
    else:
        auth_message = 'Usuário não autenticado, por favor logue novamente'
        return render(request, 'portaria/cadastrosaida.html', {'auth_message': auth_message})
#fim das views


#funcoes variadas
def get_portaria_csv(request):
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="portaria.csv"'},
    )
    writer = csv.writer(response)
    writer.writerow(['Placa','Placa2','Motorista','Empresa','Filial','Garagem','Hr_entrada','Hr_Saida'])
    cadastro = Cadastro.objects.all().values_list('placa','placa2','motorista','empresa','filial','garagem','hr_chegada','hr_saida')
    for placa in cadastro:
        writer.writerow(placa)
    return response



