from selenium import webdriver
import logging, time, os
from djcelery import celery
from django.conf import settings
from perma.tasks import save_screenshot

logger = logging.getLogger(__name__)

@celery.task
def delete_old_test_screencaps():
    """
    This func cleans up any screencaps that are 3 hours or older. It cleans
    up the mess that monitor.tasks.test_screencap creates

    This is a scheduled task. Let's have celerybeat run it.
    """

    from django.core.files.storage import FileSystemStorage
    import os
    from django.conf import settings

    dir_path = os.path.join(*[getattr(settings, 'MEDIA_ROOT'), 'monitor'])
    files = os.listdir(dir_path)

    # If the file is over three hours old and is for sure in our 'monitor'
    # path, delete it.
    for f in files:
        file_path = os.path.join(dir_path, f)
        if time.time() - os.path.getmtime(file_path) > 10800:
            if 'monitor' in file_path:
                try:
                    os.remove(file_path)
                except OSError:
                    pass


@celery.task
def test_screencap(url, disk_path):
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

    driver = webdriver.PhantomJS(executable_path=getattr(settings, 'PHANTOMJS_BINARY', 'phantomjs'),)
    driver.get(url)
    save_screenshot(driver, disk_path)

    driver.quit

    return disk_path