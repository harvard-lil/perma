from .settings import *

DATABASES['default']['NAME'] = DATABASES['default']['NAME']+'_mirror'
MIRROR_SERVER = True
