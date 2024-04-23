import os
import logging
from flask import Flask
from celery import Celery
#from apps import json_page
from dotenv import load_dotenv
import apps

load_dotenv()

log = logging.getLogger(f'{__name__}')
logging.basicConfig(filename='app.log', level=logging.INFO)


app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL','')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND','')

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'], include=['apps.json_page'])
celery.conf.update(app.config)
