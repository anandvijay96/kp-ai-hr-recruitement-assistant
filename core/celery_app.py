from celery import Celery
from core.config import settings

# Create Celery app
celery_app = Celery(
    'hr_assistant',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['tasks.resume_tasks']  # Import task modules
)

# Configure Celery
celery_app.conf.update(
    task_track_started=settings.celery_task_track_started,
    task_time_limit=settings.celery_task_time_limit,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Optional: Configure periodic tasks if needed
# from celery.schedules import crontab
# celery_app.conf.beat_schedule = {
#     'cleanup-old-resumes': {
#         'task': 'tasks.resume_tasks.cleanup_old_resumes',
#         'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
#     },
# }
