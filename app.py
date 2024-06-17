import os
import logging
from flask import Flask
from celery import Celery
#from apps import json_page
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

log = logging.getLogger(f'{__name__}')
logging.basicConfig(filename='app.log', level=logging.INFO)


app = Flask(__name__)
app.config['celery_broker_url'] = os.getenv('celery_broker_url','')
app.config['celery_result_backend'] = os.getenv('celery_result_backend','')

CORS(app)
celery = Celery(app.name, broker=app.config['celery_broker_url'], backend=app.config['celery_result_backend'], include=['apps.json_page'])
celery.conf.update(app.config)
