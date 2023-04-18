import cx_Oracle
import oracledb
import json
import os
import django
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

base_dir = settings.BASE_DIR

with open(os.path.join(base_dir, 'secrets.json')) as secret_file:
    secrets = json.load(secret_file)

def get_secret(setting, secrets=secrets):
    try:
        return secrets[setting]
    except KeyError:
        raise ImproperlyConfigured(f"Set the {setting} setting")
    
#def conndb():
#    try:
#        oracledb.init_oracle_client()
#        print('connecting...')
#        cp = oracledb.ConnectParams()
#        cp.parse_connect_string("152.67.34.112:1521/orapdb1.subnetprax02.vcnpraxioocisp0.oraclevcn.com")
#        connection = oracledb.connect(user="CONSULTA142", password="BORA241", params=cp)
#    except Exception as e:
#        print(e)
#        raise e
#    else:
#        return connection

def conndb():
    print('CONEXAO: INICIANDO')
    try:
        oracledb.init_oracle_client()
        cp = oracledb.ConnectParams()
        cp.parse_connect_string("152.67.34.112:1521/aa36d94fc8025453e05381ee640a120e.subnetprax02.vcnpraxioocisp0.oraclevcn.com")
        connection = oracledb.connect(user="CONSULTA142", password="BORA241", params=cp)
        print('CONEXAO: FINALIZADO')

    except Exception as e:
        print(e)
        raise e
    else:
        return connection

