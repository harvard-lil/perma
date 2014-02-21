try:
    from .settings import *
except ImportError, e:
    if not e.message=='No module named settings':
        raise
        
    # had to comment out this line so `import perma.settings.settings_test` would work even if settings.py didn't exist:
    #raise Exception("Settings module not found. Did you copy settings.example.py to settings.py?")
