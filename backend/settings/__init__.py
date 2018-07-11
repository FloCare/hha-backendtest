import os
conf = os.environ.get('DJANGO_CONFIGURATION')

if conf == 'Dev':
    from .dev import Dev
elif conf == 'Prod':
    from .prod import Prod
else:
    from .base import Base
