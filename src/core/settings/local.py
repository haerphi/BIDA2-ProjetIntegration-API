from .base import *

# Override default for local development
DEBUG = env('DEBUG', default=True)