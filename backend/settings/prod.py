import os
from .base import Base
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


class Prod(Base):
    import dj_database_url

    DEBUG = False
    # ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",")]
    ALLOWED_HOSTS = ['*']
    # SECRET_KEY = os.environ.get('SECRET_KEY')
    SECRET_KEY = 'INSERT_SECRET_KEY'
    DATABASES = {'default': dj_database_url.config()}

    # Password validation
    # https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

    # Todo: Revisit these
    CORS_ORIGIN_ALLOW_ALL = True
    # CORS_ORIGIN_WHITELIST = (
    #     'dashboard.flocare.health:80',
    # )

    # Todo: Revisit the REST FRAMEWORK settings for prod
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.TokenAuthentication',
        ),
        # Todo: Uncomment in production
        # 'DEFAULT_PERMISSION_CLASSES': (
        #     'rest_framework.permissions.IsAuthenticated',
        # )
    }

    # Todo: Revisit these
    # Static file management settings
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.normpath(os.path.join(Base.BASE_DIR, 'static'))
    # STATICFILES_DIRS = (
    #     os.path.join(BASE_DIR, 'staticfiles'),
    # )

    # PubNub Specific Settings
    pnconfig = PNConfiguration()
    subkey = os.environ.get("SUBKEY")
    if subkey:
        pnconfig.subscribe_key = subkey
    else:
        raise Exception('No pubnub subscribe key found')
    pubkey = os.environ.get("PUBKEY")
    if pubkey:
        pnconfig.publish_key = pubkey
    else:
        raise Exception('No pubnub publish key found')
    pnconfig.ssl = True

    PUBNUB = PubNub(pnconfig)

    # Logging related settings
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO'
            },
            'phi': {
                'handlers': ['console'],
                'level': 'INFO'
            },
            'user_auth': {
                'handlers': ['console'],
                'level': 'INFO'
            }
        },
        'handlers': Base.LOGGING_HANDLERS,
        'formatters': Base.LOGGING_FORMATTERS
    }
