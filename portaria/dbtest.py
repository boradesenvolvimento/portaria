import cx_Oracle
import oracledb
import json
import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

base_dir = settings.BASE_DIR

with open(os.path.join(base_dir, 'secrets.json')) as secret_file:
    secrets = json.load(secret_file)

def get_secret(setting, secrets=secrets):
    try:
        return secrets[setting]
    except KeyError:
        raise ImproperlyConfigured(f"Set the {setting} setting")
print('iniciando conexão')

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
    try:
        oracledb.init_oracle_client()
        print('iniciando conexão...')
        cp = oracledb.ConnectParams()
        cp.parse_connect_string("152.67.34.112:1521/aa36d94fc8025453e05381ee640a120e.subnetprax02.vcnpraxioocisp0.oraclevcn.com")
        connection = oracledb.connect(user="CONSULTA142", password="BORA241", params=cp)

    except Exception as e:
        print(e)
        raise e
    else:
        return connection

