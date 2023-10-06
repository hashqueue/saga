import os
import logging

from celery import Celery
from celery.app.log import TaskFormatter
from celery.signals import task_postrun, task_prerun

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saga.settings')
from django.conf import settings

app = Celery('saga')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@task_prerun.connect
def task_prerun_handler(task_id, *args, **kwargs):
    """
    在每次任务执行之前调度
    @param task_id: 当前任务的ID
    @param args: 当前任务的位置参数
    @param kwargs: 当前任务的关键字参数
    @return:
    """
    if kwargs.get('sender').name == 'system.tasks.send_email':
        logger = logging.getLogger(settings.TASK_LOGGER_NAME)
        file_handler = logging.FileHandler(f'{settings.TASK_LOG_DIR}/{task_id}.log', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            TaskFormatter("[%(asctime)s | %(levelname)s]: %(message)s")
        )
        logger.addHandler(file_handler)


@task_postrun.connect
def task_postrun_handler(task_id, *args, **kwargs):
    """
    在每次任务执行之后调度
    @param task_id:
    @param args:
    @param kwargs:
    @return:
    """
    if kwargs.get('sender').name == 'system.tasks.send_email':
        logger = logging.getLogger(settings.TASK_LOGGER_NAME)
        for handler in logger.handlers:
            if (isinstance(handler, logging.FileHandler) and
                    handler.baseFilename == f'{settings.TASK_LOG_DIR}/{task_id}.log'):
                logger.removeHandler(handler)
