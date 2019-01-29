import os
from .base import Base


class Dev(Base):
    DEBUG = True
    ALLOWED_HOSTS = ['*']
    SECRET_KEY = 'INSERT_SECRET_KEY'

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'flo2',
            'USER': '',
            'PASSWORD': '',
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }

    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

    CORS_ORIGIN_ALLOW_ALL = True

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.TokenAuthentication',
        ),
        # 'DEFAULT_PERMISSION_CLASSES': (
        #     'rest_framework.permissions.IsAuthenticated',
        # )
    }

    # Static file management settings
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.normpath(os.path.join(Base.BASE_DIR, 'static'))
    # STATICFILES_DIRS = (
    #     os.path.join(BASE_DIR, 'staticfiles'),
    # )

    # Logging related settings
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'request_id': {
                '()': 'log_request_id.filters.RequestIDFilter'
            }
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'logfile'],
                'level': 'INFO'
            },
            'phi': {
                'handlers': ['console', 'logfile'],
                'level': 'DEBUG'
            },
            'user_auth': {
                'handlers': ['console', 'logfile'],
                'level': 'DEBUG'
            },
            'flocarebase': {
                'handlers': ['console', 'logfile'],
                'level': 'DEBUG'
            }
        },
        'handlers': Base.LOGGING_HANDLERS,
        'formatters': Base.LOGGING_FORMATTERS
    }

    MEDIA_ROOT = '/Users/pymd/flo/backend/media/'
