try:
    from .settings import *
except ImportError, e:
    if e.message=='No module named settings':
        raise Exception("Settings module not found. Did you copy settings.example.py to settings.py?")
    raise e
