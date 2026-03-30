from .base import *

# Override default for local development
DEBUG = env('DEBUG', default=True)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
