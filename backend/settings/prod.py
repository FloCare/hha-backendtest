import os
from .base import Base


class Prod(Base):
    import dj_database_url

    DEBUG = False
    ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",")]
    SECRET_KEY = os.environ.get('SECRET_KEY')
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

    # Todo: Revisit the static file settings for prod
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.normpath(os.path.join(Base.BASE_DIR, 'static'))
    # STATICFILES_DIRS = (
    #     os.path.join(BASE_DIR, 'staticfiles'),
    # )

    # Todo: Add logging for prod
