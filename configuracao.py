# configuracao.py
from decouple import config


BASE_URL = "https://sandbox.asaas.com/api/v3"
ASAAS_API_KEY = config('ASAAS_API_KEY', default=None)
