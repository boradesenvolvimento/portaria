import asyncio
import ipdb

from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from datetime import date, datetime 

from portaria.dbtest import conndb
from portaria.views import dictfetchall
from portaria.models import JustificativaEntrega, OcorrenciaEntrega, Filiais

import tracemalloc
tracemalloc.start()

async def get_justificativas():
    conn = conndb()
    cur = conn.cursor()
    
    print("JUSTIFICATIVA: INICIANDO QUERY")
    
    cur.execute(f"""
SELECT 
    F1.GARAGEM garagem,
    F1.ID_GARAGEM id_garagem, 
    DECODE(F1.TIPO_DOCTO, 8, 'NFS', 'CTE') tipo_doc,
    F1.CONHECIMENTO,
    F1.DATA_EMISSAO,
    F1.DATA_ENTREGA,
    CASE
        WHEN F1.TIPO_DOCTO = 8 THEN TO_CHAR(BC.NFANTASIACLI)
        WHEN F1.TIPO_DOCTO = 57 THEN F1.REM_RZ_SOCIAL
    END REMETENTE,
    CASE 
        WHEN F1.TIPO_DOCTO = 8 THEN F11.REC_RZ_SOCIAL
        WHEN F1.TIPO_DOCTO = 57 THEN F1.DEST_RZ_SOCIAL
    END DESTINATARIO,
    F1.PESO,
    CASE
        WHEN F11.DT_PREV_ENTREGA IS NULL THEN '01-01-0001'
        WHEN F11.DT_PREV_ENTREGA IS NOT NULL THEN TO_CHAR(F11.DT_PREV_ENTREGA, 'DD-MM-YYYY') 
    END lead_time,
    CASE
        WHEN F1.DATA_ENTREGA = '01-JAN-0001' THEN 'NAO ENTREGUE'
        WHEN F1.DATA_ENTREGA <> '01-JAN-0001' THEN CASE
            WHEN (F1.DATA_ENTREGA - F11.DT_PREV_ENTREGA) < 0 THEN 'ADIANTADO'
            WHEN (F1.DATA_ENTREGA - F11.DT_PREV_ENTREGA) > 0 THEN 'ATRASADO'
            END
    END LEADTIME,
    CASE 
        WHEN (TRUNC((MIN(F11.DT_PREV_ENTREGA))-(SYSDATE))-1) >= 0 THEN (TRUNC((MIN(F11.DT_PREV_ENTREGA))-(SYSDATE))-1)
        WHEN (TRUNC((MIN(F11.DT_PREV_ENTREGA))-(SYSDATE))*-1) < 0 THEN 0
        WHEN F11.DT_PREV_ENTREGA IS NULL THEN 0
    END em_aberto,
    E2.DESC_LOCALIDADE || '-' || E2.COD_UF local_entreg,
    LISTAGG ((LTRIM (F4.NOTA_FISCAL,0)), ' / ') nota_fiscal                           
FROM 
    FTA001 F1,
    FTA011 F11,
    EXA002 E2,
    FTA004 F4,
    BGM_CLIENTE BC               
WHERE
    F1.LOCALID_ENTREGA = E2.COD_LOCALIDADE AND
    F1.CLIENTE_FAT = BC.CODCLI             AND
    
    F1.EMPRESA = F11.EMPRESA               AND
    F1.FILIAL = F11.FILIAL                 AND
    F1.GARAGEM = F11.GARAGEM               AND
    F1.SERIE = F11.SERIE                   AND
    F1.CONHECIMENTO = F11.CONHECIMENTO     AND
    F1.TIPO_DOCTO = F11.TIPO_DOCTO         AND
    
    F1.EMPRESA = F4.EMPRESA                AND
    F1.FILIAL = F4.FILIAL                  AND
    F1.GARAGEM = F4.GARAGEM                AND
    F1.CONHECIMENTO = F4.CONHECIMENTO      AND
    F1.SERIE = F4.SERIE                    AND
    F1.TIPO_DOCTO = F4.TIPO_DOCTO          AND
    
    F1.CARGA_ENCOMENDA IN ('CARGA DIRETA','RODOVIARIO')    AND
    F1.ID_GARAGEM NOT IN (1,23,30)                         AND
    F1.DATA_CANCELADO = '01-JAN-0001'                      AND
                                                                         
    F1.DATA_EMISSAO BETWEEN ((SYSDATE)-1) AND (SYSDATE)
GROUP BY
    F1.EMPRESA,
    F1.FILIAL,
    F1.GARAGEM,
    F1.ID_GARAGEM,
    F1.TIPO_DOCTO,
    BC.NFANTASIACLI,
    F11.REC_RZ_SOCIAL,  
    F1.CONHECIMENTO,
    F1.DATA_EMISSAO,
    F1.DATA_ENTREGA,
    F1.REM_RZ_SOCIAL,
    F1.DEST_RZ_SOCIAL,
    F1.PESO,
    F11.DT_PREV_ENTREGA,
    E2.DESC_LOCALIDADE,
    E2.COD_UF                      
                    """)
    res = dictfetchall(cur)
    cur.close()
    
    print(f"JUSTIFICATIVA: LEN({len(res)})")
    
    print(f"JUSTIFICATIVA: INICIANDO INSERT")
    await insert_to_justificativa(res)
    print(f"JUSTIFICATIVA: CONCLUIDO")
        
@sync_to_async
def insert_to_justificativa(data):
    for obj in data:
        try:
            JustificativaEntrega.objects.get(
                garagem=obj['garagem'],
                tipo_doc=obj['tipo_doc'],
                conhecimento=obj['conhecimento']
                )
        except ObjectDoesNotExist:
            del obj['leadtime']
            
            lead_time = datetime.strptime(obj['lead_time'], "%d-%m-%Y").date()
            data_entrega = obj['data_entrega'].strftime('%Y-%m-%d')
            if data_entrega == '1-01-01':
                data_entrega = datetime.strptime('0001-01-01', "%Y-%m-%d").date()
            else:
                data_entrega = datetime.strptime(data_entrega, "%Y-%m-%d").date()
            
            # Verifica se tem lead_time
            if lead_time == date(1,1,1):
                obj['em_aberto'] = 999
            # Verifica se passou do prazo
            elif lead_time < date.today():
                # Verifica se foi entregue
                if data_entrega.strftime('%d-%m-%Y') == '01-01-1':
                    obj['em_aberto'] = (date.today() - lead_time).days
                else:
                    obj['em_aberto'] = (data_entrega - lead_time).days
                
                if obj['em_aberto'] < 0:
                    obj['em_aberto'] = 0
            else:
                obj['em_aberto'] = 0
            
            if obj['em_aberto'] > 1000:
                obj['em_aberto'] = 999

            try:
                filial = Filiais.objects.get(id_garagem=obj['id_garagem'])
                obj['filial'] = filial
            except:
                pass
            
            obj['lead_time'] = lead_time

            JustificativaEntrega.objects.create(**obj)
        except Exception as e:
            print('Error:%s, error_type:%s' %(e, type(e)))

async def get_ocorrencias():
    conn = conndb()
    cur = conn.cursor()
    
    print("OCORRENCIAS: INICIANDO QUERY")
    
    cur.execute(f"""
SELECT DISTINCT
    A1.GARAGEM garagem,
    A1.NUMERO_CTRC conhecimento,
    A1.TIPO_DOCTO tp_doc,
    A2.CODIGO cod_ocor,
    A2.DESCRICAO desc_ocor,
    A1.DATA_OCORRENCIA data_ocorrencia     
FROM 
    ACA001 A1,
    ACA002 A2
WHERE
    A1.COD_OCORRENCIA = A2.CODIGO AND
    A1.DATA_CADASTRO BETWEEN ((SYSDATE)-1) AND (SYSDATE)                     
                    """)
    res = dictfetchall(cur)
    cur.close()

    print(f"OCORRENCIAS: LEN({len(res)})")
    
    print(f"OCORRENCIAS: INICIANDO INSERT")
    await insert_to_ocorrencias(res)
    print(f"OCORRENCIAS: CONCLUIDO")

@sync_to_async
def insert_to_ocorrencias(data):
    for obj in data:
        just = JustificativaEntrega.objects.filter(
                garagem=obj['garagem'], conhecimento=obj['conhecimento']).first()
        
        if just:
            obj['entrega'] = just
            data_ocorrencia = obj['data_ocorrencia'].date()
            try:
                OcorrenciaEntrega.objects.get(**obj)
            except ObjectDoesNotExist:
                # Verifica a ocorrencia é com descrição "Entregue"
                if obj['desc_ocor'] == 'Entregue':
                    just.data_entrega = data_ocorrencia
                    if (just.data_entrega - just.lead_time).days <= 0:
                        just.em_aberto = 0
                    else:
                        just.em_aberto = (just.data_entrega - just.lead_time).days
                # Verifica se tem lead_time
                elif just.lead_time.strftime('%d-%m-%Y') != '01-01-0001':
                    # Verifica se não tem data_entrega
                    if just.data_entrega.strftime('%d-%m-%Y') == '01-01-0001':
                        just.em_aberto = (data_ocorrencia - just.lead_time).days
                        if just.em_aberto < 0:
                            just.em_aberto = 0
                
                if just.em_aberto > 1000:
                    just.em_aberto = 999
                
                just.save()
                
                try:
                    obj['filial'] = just.filial
                except:
                    pass
                
                OcorrenciaEntrega.objects.create(**obj)
            except Exception as e:
                print('Error:%s, error_type:%s' %(e, type(e)))

asyncio.run(get_justificativas())
asyncio.run(get_ocorrencias())
