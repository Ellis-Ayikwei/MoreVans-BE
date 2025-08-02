"""
Celery configuration for Waste Wise project.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('waste_wise')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    # Process sensor data every minute
    'process-sensor-data': {
        'task': 'apps.sensors.tasks.process_sensor_queue',
        'schedule': crontab(minute='*'),
    },
    # Check for full bins every 5 minutes
    'check-bin-levels': {
        'task': 'apps.alerts.tasks.check_bin_levels',
        'schedule': crontab(minute='*/5'),
    },
    # Optimize routes every hour
    'optimize-routes': {
        'task': 'apps.routes.tasks.optimize_collection_routes',
        'schedule': crontab(minute=0),
    },
    # Generate daily analytics report
    'daily-analytics': {
        'task': 'apps.analytics.tasks.generate_daily_report',
        'schedule': crontab(hour=0, minute=0),
    },
    # Clean old sensor data weekly
    'cleanup-old-data': {
        'task': 'apps.sensors.tasks.cleanup_old_readings',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),
    },
    # Predict fill levels every 30 minutes
    'predict-fill-levels': {
        'task': 'apps.analytics.tasks.predict_fill_levels',
        'schedule': crontab(minute='*/30'),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')