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
    path('paletes/', views.PaleteView.as_view(), name='paleteview'),
    path('paletes/transfpaletes/', views.transfpalete, name='transfpaletes'),
    path('frota/', views.frota, name='frota'),
    path('frota/<str:placa_id>&<moto_id>/checklist/', views.checklistfrota, name='checklistfrota'),
    path('manutencaofrota/', views.manutencaofrota, name='manutencaofrota'),
    path('manutencaofrota/<str:placa_id>/manuentrada/', views.manuentrada, name='manuentrada'),
    path('manutencaofrota/<int:osid>/manusaida/', views.manusaida, name='manusaida'),
    path('manutencaofrota/manutencaoview/', views.ManutencaoListView.as_view(), name='manutencaoview'),
    path('manutencaofrota/<int:osid>/manutencaoprint', views.manutencaoprint, name='manutencaoprint'),
    path('manutencaofrota/manutencaoview/pendencia', views.manupendentes, name='manupendentes'),
    path('servicospj/', views.servicospj, name='servicospj'),
    path('servicospj/<int:args>/cadservicospj/', views.cadservicospj, name='cadservicospj'),
    path('servicospj/consultanfpj/', views.consultanfpj, name='consultanfpj'),
    path('outputs/', views.outputs, name='outputs'),
    path(r'export-csv-nfpj/', views.get_nfpj_csv, name='get_nfpj_csv'),
    path(r'export-csv-port/', views.get_portaria_csv, name='get_portaria_csv'),
    path(r'export-csv-palete/', views.get_palete_csv, name='get_palete_csv'),
    path(r'export-csv-manu/', views.get_manu_csv, name='get_manu_csv'),
    path('cardusuario/', views.cardusuario, name="cardusuario"),
    path('cardusuario/<int:id>/card', views.card, name="card"),
    path('telausuariorodrigo/', views.telausuariorodrigo, name='telausuariorodrigo'),
    path('telausuariothiago/', views.telausuariothiago, name='telausuariothiago')

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)