from decouple import config

if config('MODE') == 'development':
    from .local import *
else:
    from .production import *