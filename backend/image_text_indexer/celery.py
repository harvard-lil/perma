from __future__ import absolute_import

import sys, os
from celery import Celery

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

celery = Celery('backend.image_text_indexer.celery',
                broker='amqp://guest@localhost//',
                include=['backend.image_text_indexer.tasks'])

# Optional configuration, see the application user guide.
celery.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    celery.start()