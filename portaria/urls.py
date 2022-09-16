from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'portaria'
urlpatterns = [
    path('', views.index, name='index'),
    path('portariaview/', views.Visualizacao.as_view(), name='visualizacao'),
    path('portaria/', views.cadastro, name='cadastro'),
    path('cadastro/cadastroentrada/', views.cadastroentrada, name='cadastroentrada'),
    path('cadastro/cadastrosaida/', views.cadastrosaida, name='cadastrosaida'),
    path('paletes/', views.paleteview, name='paleteview'),
    path('paletes/transfpaletes/', views.transfpalete, name='transfpaletes'),
    path('paletes/cadastro', views.cadpaletes, name='cadpaletes'),
    path('paletes/painelcliente', views.paletecliente, name='paletecliente'),
    path('paletes/saidapaletes', views.saidapalete, name='saidapalete'),
    #path('frota/', views.frota, name='frota'),
    #path('frota/<str:placa_id>&<moto_id>/checklist/', views.checklistfrota, name='checklistfrota'),
    #path('frota/checklistview/', views.checklistview, name='checklistview'),
    #path('frota/checklistview/<int:idckl>/detalhe', views.checklistdetail, name='checklistdetail'),
    #path('frota/cadastros', views.frotacadastros, name='frotacadastros'),
    #path('cadastros/motorista', views.cadmotorista, name='cadmotorista'),
    #path('cadastros/veiculo', views.cadveiculo, name='cadveiculo'),
    #path('cadastros/tipo_servico', views.cadtpservico, name='cadtpservico'),
    #path('manutencao/', views.manutencaofrota, name='manutencaofrota'),
    #path('manutencao/<str:placa_id>/entrada/', views.manuentrada, name='manuentrada'),
    #path('manutencao/<int:osid>/saida/', views.manusaida, name='manusaida'),
    #path('manutencao/view/', views.ManutencaoListView.as_view(), name='manutencaoview'),
    #path('manutencao/<int:osid>/print', views.manutencaoprint, name='manutencaoprint'),
    #path('manutencao/view/pendencia', views.manupendentes, name='manupendentes'),
    #path('manutencao/agendamento', views.agendamentomanu, name='agendamentomanu'),
    #path('manutencao/<osid>/update', views.updatemanu, name='updatemanu'),
    #path('manutencao/<osid>/addservico', views.addservico, name='addservico'),
    path('servicospj/', views.servicospj, name='servicospj'),
    path('servicospj/<int:args>/cadastro/', views.cadservicospj, name='cadservicospj'),
    path('servicospj/consulta/', views.consultanfpj, name='consultanfpj'),
    path('decimopj/', views.decimopj, name='decimopj'),
    path('decimopj/<int:idfunc>/parcela1', views.caddecimo1, name='caddecimo1'),
    path('decimopj/<int:idfunc>/parcela2', views.caddecimo2, name='caddecimo2'),
    path('decimopj/view', views.decimoview, name='decimoview'),
    path('feriaspj/', views.feriaspjv, name='feriaspjv'),
    path('feriaspj/cadastro', views.feriascad, name='feriascad'),
    path('feriaspj/view', views.feriasview, name='feriasview'),
    path('feriaspj/<int:idfpj>/agendamento', views.feriasagen, name='feriasagen'),
    path('feriaspj/<int:idfpj>/quitar', views.feriasquit, name='feriasquit'),
    path('cadastro-funcionariopj/', views.cadfuncionariopj, name='cadfuncionariopj'),
    path('atualizar-funcionariopj/', views.atualizarfunc, name='atualizarfunc'),
    path('fatferramentas/', views.fatferramentas, name='fatferramentas'),
    #path('paineltickets/', views.tktmetrics, name='tktmetrics'),
    #path('tickets/', views.monitticket, name='monitticket'),
    #path('tickets/new/', views.tktcreate, name='tktcreate'),
    #path('tickets/<tktid>/', views.closetkt, name='closetkt'),
    #path('tickets/<tktid>/view/', views.tktview, name='tktview'),
    #path('tickets/includemail', views.includemailtkt, name='includemailtkt'),
    path('etiquetas', views.etiquetas, name='etiquetas'),
    path('contagem-etiquetas/', views.contagemetiquetas, name='contagemetiquetas'),
    path(r'contagem-etiquetas/bipagem/', views.bipagemetiquetas, name='bipagemetiquetas'),
    path('retorno-etiquetas', views.retornoetiqueta, name='retornoetiqueta'),
    path(r'pdf/', views.createetiquetas, name='createetiquetas'),
    path('etiquetas_palete/', views.etiquetas_palete, name='etiquetas_palete'),
    path('bipagem_palete/', views.bipagem_palete, name='bipagem_palete'),
    path('etiqueta_relatorio/', views.etqrelatorio, name='etqrelatorio'),
    path('romaneioop/', views.romaneioxml, name='romaneioxml'),
    path('romaneioop/painel/', views.painelromaneio, name='painelromaneio'),
    path('romanieoop/xml-manual', views.entradaromaneio, name='entradaromaneio'),
    path('handler-xml/', views.entradaxml, name='entradaxml'),
    path('chamados/', views.chamado, name='chamado'),
    path('chamados/novo', views.chamadonovo, name='chamadonovo'),
    path('chamados/painel', views.chamadopainel, name='chamadopainel'),
    path('chamados/painel/<tktid>/detalhes', views.chamadodetail, name='chamadodetail'),
    path('chamados/concluidos', views.chamado_concluido, name='chamadoconcluido'),
    path('chamados/chamadoreadmail', views.chamadoreadmail, name='chamadoreadmail'),
    path('replymail_monitoramento/<tktid>', views.replymail_monitoramento, name='replymail_monitoramento'),
    path(r'mailferias/<int:idfpj>', views.mailferias, name='mailferias'),
    path('justificativa/', views.justificativa, name='justificativa'),
    path('relatorios-just/', views.rel_justificativa, name='rel_justificativa'),
    path('confirmar-just/', views.confirmjust, name='confirmjust'),
    path(r'edibuilder/', views.ediexceltosd1, name='ediexceltosd1'),
    path(r'ediexample/', views.exedicorreios, name='exedicorreios'),
    path('export-bipagem/', views.bipagemdocrel, name='bipagemdocrel'),
    path('export-bipagem-palete/', views.bipagempalrel, name='bipagempalrel'),
    path(r'export-mail-nfpj/', views.get_nfpj_mail, name='get_nfpj_mail'),
    path(r'export-csv-nfpj/', views.get_nfpj_csv, name='get_nfpj_csv'),
    path(r'export-csv-port/', views.get_portaria_csv, name='get_portaria_csv'),
    path(r'export-csv-palete/', views.get_palete_csv, name='get_palete_csv'),
    path(r'export-csv-manu/', views.get_manu_csv, name='get_manu_csv'),
    path(r'export-13-pj/', views.get_pj13_mail, name='get_pj13_mail'),
    path(r'export-13-pj-csv/', views.get_pj13_csv, name='get_pj13_csv'),
    path(r'export-checklist-csv/', views.get_checklist_csv, name='get_checklist_csv'),
    path(r'export-ferias-csv/', views.get_ferias_csv, name='get_ferias_csv'),
    path('export-retornorom/', views.retornoromcsv, name='retornoromcsv'),
    #path(r'readmail/', views.readmail_monitoramento, name="readmail_monitoramento"),
    path('cardusuario/', views.cardusuario, name='cardusuario'),
    path('cardusuario/<int:id>/card', views.card, name='card'),
    path(r'readnotify/<notifyid>/', views.isnotifyread, name='isnotifyread'),
    path(r'allreadnotify/<user>', views.setallread, name='setallread'),
    path(r'vncmtnotifymanu/', views.notifymanutencaovencidos, name='notifymanutencaovencidos'),
    path('mdfeporfilial/', views.mdfeporfilial, name='mdfeporfilial'),
    path(r'modaltkt/', views.modaltkt, name='modaltkt'),
    path('get_justificativas/', views.get_justificativas, name='get_justificativas'),
    path('get_ocorrencias/', views.get_ocorrencias, name='get_ocorrencias'),
    path('getxmlsapi/', views.get_xmls_api, name='getxmlsapi'),
    path('compras/', views.compras_index, name='compras_index'),
    path('compras/lancar_pedido/', views.compras_lancar_pedido, name='compras_lancar_pedido'),
    path('compras/painel/', views.painel_compras, name='painel_compras'),
    path('compras/painel/<id>/edit', views.edit_compras, name='edit_compras'),
    #path('insert_entradas_cpr/', views.insert_entradas_cpr, name='insert_entradas_cpr'),
    path('estoque/', views.estoque_index, name='estoque_index'),
    path('estoque/solicitacoes', views.estoque_painel, name='estoque_painel'),
    path('estoque/nova_solicitacao/', views.estoque_nova_solic, name='estoque_nova_solic'),
    path('estoque/itens/listagem', views.estoque_listagem_itens, name='estoque_listagem_itens'),
    path('estoque/itens/listagem/<id>/edit', views.estoque_detalhe, name='estoque_detalhe'),
    path('estoque/itens/listagem/cadastrar', views.estoque_caditem, name='estoque_caditem'),
    path('estoque/confirma', views.estoque_confirma_item, name='estoque_confirma_item'),
    path('demissoes/', views.index_demissoes, name='demissoes'),
    path('demissoes/get_funcionarios_demissao/', views.get_funcionarios_demissao, name='get_funcionarios_demissao'),
    #path('terceirizados/', views.terceirizados_index, name='terceirizadosindex'),
    #path('terceirizados/insert', views.insert_terceirizados, name='insertterceirizados'),
    #path('terceirizados/saidas', views.saidas_terceirizados, name='saidas_terceirizados'),
    #path('get_terceirizados_xls', views.get_terceirizados_xls, name='get_terceirizados_xls'),
    path('sugestoes/', views.sugestoesedenuncias, name='sugestoesedenuncias')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)