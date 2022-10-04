"""
Django settings for verkeersvergunningen project.

Generated by 'django-admin startproject' using Django 3.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
from pathlib import Path

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

DECOS_BASE_URL = os.getenv('DECOS_BASE_URL', 'https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/')
ZWAAR_VERKEER_ZAAKNUMMER = os.getenv('ZWAAR_VERKEER_ZAAKNUMMER', '8A02814D73B3421B9C65262A45A43BD8')
TAXI_BSN_ZAAKNUMMER = os.getenv('TAXI_BSN_ZAAKNUMMER', '1829F53FD9754B91ADC0B7D16E1519AD')
TAXI_ZONE_ONTHEFFING_ZAAKNUMMER = os.getenv('TAXI_ZONE_ONTHEFFING_ZAAKNUMMER', 'D379EC92DE114A8E92A22FD0E7EFB4E6')
TAXI_HANDHAVINGSZAKEN_ZAAKNUMMER = os.getenv('TAXI_HANDHAVINGSZAKEN_ZAAKNUMMER', '496E3E505C4045BAB5286B56CF2FC89E')
DECOS_BASIC_AUTH_USER = os.getenv('DECOS_BASIC_AUTH_USER')
DECOS_BASIC_AUTH_PASS = os.getenv('DECOS_BASIC_AUTH_PASS')
DECOS_TAXI_AUTH_USER = os.getenv('DECOS_TAXI_AUTH_USER')
DECOS_TAXI_AUTH_PASS = os.getenv('DECOS_TAXI_AUTH_PASS')
CLEOPATRA_BASIC_AUTH_USER = os.environ['CLEOPATRA_BASIC_AUTH_USER']
CLEOPATRA_BASIC_AUTH_PASS = os.environ['CLEOPATRA_BASIC_AUTH_PASS']

BASICAUTH_USERS = {CLEOPATRA_BASIC_AUTH_USER: CLEOPATRA_BASIC_AUTH_PASS}

ALLOWED_HOSTS = ['*']
INTERNAL_IPS = ('127.0.0.1', '0.0.0.0')


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'drf_yasg',
    'taxi',
    'zwaarverkeer',
    'health',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ROOT_URLCONF = 'main.urls'
BASE_URL = os.getenv('BASE_URL', '')
FORCE_SCRIPT_NAME = BASE_URL

WSGI_APPLICATION = 'main.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Amsterdam'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = BASE_URL + '/static/'
STATIC_ROOT = '/static/'

SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        ignore_errors=['ExpiredSignatureError'],
    )
