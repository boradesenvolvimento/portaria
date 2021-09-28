from django.urls import path
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
    path('frota/checklist/', views.checklistfrota, name='checklistfrota'),
    path('outputs/', views.outputs, name='outputs'),
    path(r'export-csv-port/', views.get_portaria_csv, name='get_portaria_csv'),
    path(r'export-csv-palet/', views.get_palet_csv, name='get_palet_csv')

]