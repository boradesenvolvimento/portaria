import os
from celery import Celery

#Set the default Django module from the 'celery' program.
from django.contrib import messages
from notifications.signals import notify

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
app = Celery('mysite')

#Using a string here means the worker will not have to pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task
def readmailasync():
    import poplib, re, email, datetime
    from django.conf import settings
    from email import policy
    from portaria.models import EmailMonitoramento, TicketMonitoramento
    from django.contrib.auth.models import User
    attatch = ''
    host = 'pop.kinghost.net'
    e_user = 'bora@bora.tec.br'
    e_pass = 'Bor@dev#123'
    print('iniciando readmail')
    pp = poplib.POP3(host)
    pp.set_debuglevel(1)
    pp.user(e_user)
    pp.pass_(e_pass)
    pattern1 = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp)')
    pattern2 = re.compile(r'[^\"]+(?i:jpeg|jpg|gif|png|bmp).\w+.\w+')
    num_messages = len(pp.list()[1])
    for i in range(num_messages):
        # acessa o poplib e pega os emails
        try:
            raw_email = b'\n'.join(pp.retr(i + 1)[1])
            parsed_email = email.message_from_bytes(raw_email, policy=policy.compat32)
        except Exception as e:
            print(f'parsed -- ErrorType: {type(e).__name__}, Error: {e}')
        else:
            if parsed_email.is_multipart():
                for part in parsed_email.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get('Content-Type'))
                    if ctype == 'text/plain' and 'attatchment' not in cdispo:
                        body = part.get_payload(decode=True)
                    elif ctype == 'text/html' and 'attatchment' not in cdispo:
                        body = part.get_payload(decode=True)
                    if ctype == 'text/html' and 'attatchment' not in cdispo:
                        htbody = part.get_payload(decode=True)
                    filename = part.get_filename()
                    hoje = datetime.date.today()
                    # verifica se existem arquivos no email
                    if filename:
                        path = settings.MEDIA_ROOT + '/django-summernote/' + str(hoje) + '/'
                        locimg = os.path.join(settings.MEDIA_ROOT + '/django-summernote/' + str(hoje) + '/', filename)
                        if os.path.exists(os.path.join(path)):
                            fp = open(locimg, 'wb')
                            fp.write(part.get_payload(decode=True))
                            fp.close()
                        else:
                            os.mkdir(path=path)
                            fp = open(locimg, 'wb')
                            fp.write(part.get_payload(decode=True))
                            fp.close()
                        item = os.path.join('/media/django-summernote/' + str(hoje) + '/', filename)
                        aa = '<div class="mailattatch"><a href="' + item + '" download><img src="/static/images/downicon.png" width="40"><p>' + filename + '</p></a></div>'
                        attatch += aa
            else:
                body = parsed_email.get_payload(decode=True)
            cs = parsed_email.get_charsets()
            for q in cs:
                if q is None:
                    continue
                else:
                    cs = q
            # pega parametros do email
            try:
                e_date = datetime.datetime.strptime(parsed_email['Date'], '%a, %d %b %Y %H:%M:%S %z').strftime(
                    '%Y-%m-%d')
                print(e_date)
                e_title = parsed_email['Subject']
                e_from = parsed_email['From']
                if re.findall(r'<(.*?)>', e_from): e_from = re.findall(r'<(.*?)>', e_from)[0]

                e_to = parsed_email['To']
                if re.findall(r'<(.*?)>', e_to): e_to = re.findall(r'<(.*?)>', e_to)[0]
                e_cc = parsed_email['CC']
                if e_cc:
                    if re.findall(r'<(.*?)>', e_cc): e_cc = re.findall(r'<(.*?)>', e_cc)[0]

                e_id = parsed_email['Message-ID']
                e_ref = parsed_email['References']
                if e_ref is None: e_ref = e_id
                if e_ref is not None: e_ref = e_ref.split(' ')[0]
                # converte o corpo do email
                e_body = body.decode(cs)
                if e_body:
                    reply_parse = re.findall(
                        r'(De:+\s+\w.*.\sEnviada em:+\s+\w.*.+[,]+\s+\d+\s+\w+\s+\w+\s+\w+\s+\d+\s+\d+:+\d.*)', e_body)
                    if reply_parse:
                        e_body = e_body.split(reply_parse[0])[0].replace('\n', '<br>')
                w_body = htbody.decode(cs)
                if w_body:
                    reply_html = re.findall(
                        r'(<b><span+\s+\w.*.[>]+De:.*.Enviada em:.*.\s+\w.*.[,]+\s+\d+\s+\w+\s+\w+\s+\w+\s+\d+\s+\d+:+\d.*)',
                        w_body)
                    if reply_html:
                        w_body = w_body.split(reply_html[0])[0]

                if re.findall(pattern2, w_body):
                    for q in re.findall(pattern2, w_body):
                        new = re.findall(pattern1, q)
                        teste = os.path.join(settings.MEDIA_URL + 'django-summernote/' + str(hoje) + '/',
                                             new[0].split('cid:')[1])
                        w_body = w_body.replace(q, teste)
                elif re.findall(pattern1, w_body):
                    for q in re.findall(pattern1, w_body):
                        new = re.findall(pattern1, q)
                        try:
                            teste = os.path.join(settings.MEDIA_URL + 'django-summernote/' + str(hoje) + '/',
                                                 new[0].split('cid:')[1])
                        except Exception as e:
                            print(f'ErrorType: {type(e).__name__}, Error: {e}')
                        else:
                            w_body = w_body.replace(q, teste)

            except Exception as e:
                print(f'insert data -- ErrorType: {type(e).__name__}, Error: {e}')
            else:
                # salva no banco de dados
                form = EmailMonitoramento.objects.filter(email_id=e_ref)
                sender = User.objects.get(username='admin')
                if form.exists() and form[0].tkt_ref.status != ('CONCLUIDO' or 'CANCELADO'):
                    xxx = form[0].ult_resp_html
                    if xxx: zzz = w_body.split(xxx[:50])
                    try:
                        tkt = TicketMonitoramento.objects.get(pk=form[0].tkt_ref_id)
                        notify.send(sender, recipient=tkt.responsavel, verb='message',
                                    description=f"Você recebeu uma nova mensagem do ticket {tkt.id}")
                    except Exception as e:
                        print(f'ErrorType: {type(e).__name__}, Error: {e}')
                    if form[0].ult_resp is not None:
                        aa = '<hr>' + e_from + ' -- ' + e_date + '\n' + e_body + '\n------Anterior-------\n' + form[
                            0].ult_resp
                        bb = '<hr>' + e_from + ' -- ' + e_date + '<br>' + zzz[0] + attatch + '<hr>' + form[0].ult_resp_html
                    else:
                        aa = '<hr>' + e_from + ' -- ' + e_date + '\n' + e_body
                        bb = '<hr>' + e_from + ' -- ' + e_date + '<br>' + w_body + attatch
                    if tkt.status == 'ABERTO':
                        TicketMonitoramento.objects.filter(pk=form[0].tkt_ref_id).update(status='ANDAMENTO')
                    form.update(ult_resp=aa, ult_resp_html=bb, ult_rest_dt=e_date)
                    pp.dele(i + 1)
                elif form.exists() and form[0].tkt_ref.status == ('CONCLUIDO' or 'CANCELADO'):
                    pp.dele(i + 1)
                    pp.quit()
                else:
                    try:
                        tkt = TicketMonitoramento.objects.get(msg_id=e_ref)
                    except Exception as e:
                        print(f'ErrorType: {type(e).__name__}, Error: {e}')
                    else:
                        bb = '<hr>' + e_from + ' -- ' + e_date + w_body
                        EmailMonitoramento.objects.create(assunto=e_title, mensagem=bb, cc=e_cc, dt_envio=e_date,
                                                          email_id=tkt.msg_id, tkt_ref_id=tkt.id)
                        notify.send(sender, recipient=tkt.responsavel, verb='message',
                                    description="Seu ticket foi criado.")
                    pp.dele(i + 1)
    pp.quit()

app.conf.beat_schedule = {
    'run_every_min_readmail':{
        'task':'mysite.celery.readmailasync',
        'schedule': 60
    }
}