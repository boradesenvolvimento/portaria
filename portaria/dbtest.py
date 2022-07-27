import cx_Oracle
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
def conndb():
    try:
        conn = cx_Oracle.connect(get_secret('ORA_UID'),get_secret('ORA_PWD'), cx_Oracle.makedsn(get_secret('ORA_HOST'), '1521', None, get_secret('ORA_XE')))
    except Exception as e:
        raise e
    else:
        return conn
