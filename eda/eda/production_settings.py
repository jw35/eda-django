import os

from eda.settings import *

from eda.production_secrets import *

DEBUG = True

ALLOWED_HOSTS = ['*']

STATIC_ROOT = STATIC_ROOT = os.path.join(BASE_DIR, "static")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = "jon.warbrick@googlemail.com"
EMAIL_HOST_PASSWORD = EMAIL_PASSWORD
EMAIL_PORT = 587
EMAIL_USE_TLS = True

