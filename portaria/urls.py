from django.urls import path
from . import views

app_name = 'portaria'
urlpatterns = [
    path('', views.index, name='index'),
    path('visualizacao/', views.Visualizacao.as_view(), name='visualizacao'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('cadastro/cadastroentrada/', views.cadastroentrada, name='cadastroentrada'),
    path('cadastro/<str:placa_id>/cadastrosaida/', views.cadastrosaida, name='cadastrosaida'),
    path(r'export-csv/', views.get_portaria_csv, name='get_portaria_csv')

]