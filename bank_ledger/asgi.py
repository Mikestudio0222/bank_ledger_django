"""
ASGI config for bank_ledger project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bank_ledger.settings')

application = get_asgi_application()
