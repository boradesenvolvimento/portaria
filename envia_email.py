import tracemalloc
import os
import django
from django.core.mail import send_mail

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

tracemalloc.start()

def envia_email(data: dict):
    escrita = ""
    try:
        if data['entradas']:
            nova_linha = "\n"
            escrita = nova_linha.join(f"ID - {entrada.id}: {entrada.obs}"for entrada in data['entradas'])
            escrita = escrita.replace('<p>', '')
            escrita = escrita.replace('</p>', '')
            escrita = escrita.replace('<br>', '')
            escrita = escrita.replace('</br>', '')
            escrita = escrita.replace('</br>', '')
            escrita = escrita.replace('att&nbsp;', '')
            escrita = escrita.replace('&nbsp;', '')

        body_email = {
            "subject": f"Atualização da Solicitação: {data['nr_pedido']}",
            "message": f"""
    STATUS: {data['status']}
    SOLICITAÇÃO: {data['nr_pedido']}
    CATEGORIA: {data['categoria'] if data['categoria'] == "" else "NÃO INFORMADO"}
    DATA: {data['data']}
    RESPONSÁVEL: {data['responsavel'] or "NÃO INFORMADO"}


    ENTRADAS:
    {escrita or "NÃO INFORMADO"}


    OBSERVAÇÃO:
    {data['observacao'] or "NÃO INFORMADO"}


    Atenciosamente,
    Bora Desenvolvimento.
                """,
                "from_email": "solicitacoes.compra@bora.tec.br",
                "recipient_list": [data['email_solicitante']],
            }
        send_mail(**body_email)
        return True
    except Exception as e:
        print(e)
        return False