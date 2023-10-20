
from django.core.management.base import BaseCommand

from dojo.models import Finding, Notes
# from dojo.utils import get_system_setting, do_dedupe_finding, dojo_async_task
from dojo.celery import app
from functools import wraps
from dojo.utils import test_valentijn


class Command(BaseCommand):
    help = "Command to do some tests with celery and decorators. Just committing it so 'we never forget'"

    def handle(self, *args, **options):
        finding = Finding.objects.all().first()

        test_valentijn(finding, Notes.objects.all().first())


def test2(clazz, id):
    model = clazz.objects.get(id=id)
    print(model)


def my_decorator_outside(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("outside before")
        func(*args, **kwargs)
        print("outside after")

    if getattr(func, 'delay', None):
        wrapper.delay = my_decorator_outside(func.delay)

    return wrapper


def my_decorator_inside(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("inside before")
        func(*args, **kwargs)
        print("inside after")
    return wrapper


@my_decorator_outside
@app.task
@my_decorator_inside
def my_test_task(new_finding, *args, **kwargs):
    print('test task...')


# example working with multiple parameters...
@dojo_model_to_id(parameter=1)
@dojo_model_to_id
@dojo_async_task
@app.task
@dojo_model_from_id(model=Notes, parameter=1)
@dojo_model_from_id
def test_valentijn_task(new_finding, note):
    logger.debug('test_valentijn:')
    logger.debug(new_finding)
    logger.debug(note)
