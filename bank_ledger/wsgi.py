"""
WSGI config for bank_ledger project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bank_ledger.settings')

application = get_wsgi_application()
