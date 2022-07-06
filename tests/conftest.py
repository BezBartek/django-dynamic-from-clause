import os

from django.conf import settings
import environ


env = environ.Env()
env.read_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


def pytest_configure():
    """Configure a django settings"""
    settings.configure(
        DATABASES={
            "default": {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': env('POSTGRES_DB'),
                'USER': env('POSTGRES_USER'),
                'PASSWORD': env('POSTGRES_PASSWORD'),
                'HOST': env('POSTGRES_HOST'),
                'PORT': env('POSTGRES_PORT'),
            },
        },
        INSTALLED_APPS=[
            "tests.test_app",
        ],
    )
