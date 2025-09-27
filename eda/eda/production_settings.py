import os

from eda.settings import *

from eda.production_secrets import *

DEBUG = True

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = ['']

STATIC_ROOT = STATIC_ROOT = os.path.join(BASE_DIR, "static")

