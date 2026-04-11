from .base import *

# Production overrides
DEBUG = env('DEBUG', default=False)

# Make sure ALLOWED_HOSTS is read from env or securely defined
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
