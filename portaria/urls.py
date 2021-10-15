from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'portaria'
urlpatterns = [
    path('', views.index, name='index'),
    path('visualizacao/', views.Visualizacao.as_view(), name='visualizacao'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('cadastro/cadastroentrada/', views.cadastroentrada, name='cadastroentrada'),
    path('cadastro/cadastrosaida/', views.cadastrosaida, name='cadastrosaida'),
    path('palets/', views.PaletView.as_view(), name='paletview'),
    path('palets/transfpalets', views.transfpalet, name='transfpalets'),
    path('frota/', views.frota, name='frota'),
    path('frota/<str:placa_id>/checklist/', views.checklistfrota, name='checklistfrota'),
    path('servicospj/', views.servicospj, name='servicospj'),
    path('servicospj/<args>/cadservicospj/', views.cadservicospj, name='cadservicospj'),
    path('outputs/', views.outputs, name='outputs'),
    path(r'export-csv-nfpj', views.get_nfpj_csv, name='get_nfpj_csv'),
    path(r'export-csv-port/', views.get_portaria_csv, name='get_portaria_csv'),
    path(r'export-csv-palet/', views.get_palet_csv, name='get_palet_csv'),
    path('telausuariorodrigo/', views.telausuariorodrigo, name='telausuariorodrigo'),
    path('telausuariothiago/', views.telausuariothiago, name='telausuariothiago')

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)