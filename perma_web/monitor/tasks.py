from selenium import webdriver
import logging
from datetime import datetime
from io import BytesIO
from celery import shared_task

from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.conf import settings


logger = logging.getLogger(__name__)

@shared_task
def delete_screencaps():
    """
    This func cleans up any screencaps that are 3 hours or older. It cleans
    up the mess that monitor.tasks.test_screencap creates

    This is a scheduled task. Let's have celerybeat run it.
    """

    upload_storage = FileSystemStorage(location=getattr(settings, 'MONITOR_ROOT'))
    files = upload_storage.listdir(getattr(settings, 'MONITOR_ROOT'))[1]

    # If the file is over three hours old, delete it.
    for f in files:
        age_of_file = datetime.now() - upload_storage.created_time(f)
        if  age_of_file.seconds > 10800:
            upload_storage.delete(f)


@shared_task
def get_screencap(url, file_name):
    """
    This func helps monitor our Celery/Selenium/PhantomJS image
    creation process. We'll use this to coarsely keep tabs on the availability
    of our "create new archive" service.

    Returns the image (png) capture

    NOTE: This func does not permanently store anything. It should only be used
    for monitoring purposes.

    TODO: this should replicate everything that happens in proxy_capture, flesh
    this out.
    """

    # We don't want to mix this monitoring stuff with our user generated media (archives)
    monitor_storage = FileSystemStorage(location=getattr(settings, 'MONITOR_ROOT'))

    driver = webdriver.PhantomJS(executable_path=getattr(settings, 'PHANTOMJS_BINARY', 'phantomjs'),)
    driver.get(url)

    file_object = BytesIO(driver.get_screenshot_as_png())
    file = File(file_object)

    driver.quit

    monitor_storage.save(file_name, file)