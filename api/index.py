import os
import sys
from pathlib import Path

# Add backend directory to Python path so Django settings and apps can be imported
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / 'backend'

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Default to production settings for Vercel deployment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

from django.core.wsgi import get_wsgi_application

# Vercel Serverless WSGI application entry point
application = get_wsgi_application()

# Alias 'app' for Vercel Python runtime
app = application
