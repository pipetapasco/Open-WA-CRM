"""
Celery Configuration for Open-WA-CRM
Este módulo configura Celery para el procesamiento asíncrono
de mensajes de WhatsApp.
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Bogota',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos máximo por tarea
    worker_prefetch_multiplier=1,  # Para tareas largas de WhatsApp
    task_acks_late=True,  # Confirmar tarea solo cuando termine
)

# Rutas de tareas por prioridad
app.conf.task_routes = {
    'whatsapp.*': {'queue': 'whatsapp'},
    'messages.*': {'queue': 'messages'},
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
