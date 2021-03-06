"""
Django settings for daesun project.

Generated by 'django-admin startproject' using Django 1.10.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'x-g(o_(ep7rhy+h7w5*zpjey4cb818z5&@+8y+yf*jc)#5j)+0'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# DEBUG = False

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'apis.apps.ApisConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',
    'web',
]

MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',     # This must be first on the list
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',  # This must be last
]

ROOT_URLCONF = 'daesun.urls'

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

WSGI_APPLICATION = 'daesun.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
# [START dbconfig]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'daesun',
        'USER': 'daesun',
        'PASSWORD': 'aabb1122',
    }
}
# In the flexible environment, you connect to CloudSQL using a unix socket.
# Locally, you can use the CloudSQL proxy to proxy a localhost connection
# to the instance
DATABASES['default']['HOST'] = '/cloudsql/daesun2017:asia-east1:mysql'
if os.getenv('GAE_INSTANCE'):
    pass
else:
    DATABASES['default']['HOST'] = '127.0.0.1'
# [END dbconfig]

DATABASE_OPTIONS = {'charset': 'utf8'}

CACHES = {
    'default': {
        # 'BACKEND': 'redis_cache.RedisCache',
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'LOCATION': [
            '104.199.215.251:6379',
        ],
        'OPTIONS': {
            'DB': 1,
            'PASSWORD': 'aabb1122',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            },
            'MAX_CONNECTIONS': 1000,
            'PICKLE_VERSION': -1,
        },
    },
    'memcached': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '104.199.215.251:11211',
    }
}

if os.getenv('GAE_INSTANCE'):
    if os.environ.get('USE_GAE_MEMCACHE'):
        CACHES['memcached']['LOCATION'] = '127.0.0.1:11211'

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'ko-kr'

TIME_ZONE = 'Asia/Seoul'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

# Fill in your cloud bucket and switch which one of the following 2 lines
# is commented to serve static content from GCS
# STATIC_URL = 'https://storage.googleapis.com/<your-gcs-bucket>/static/'

if os.getenv('GAE_INSTANCE'):
    STATIC_URL = 'https://storage.googleapis.com/daesun2017.appspot.com/static/'
    MEDIA_URL = 'https://storage.googleapis.com/daesun2017.appspot.com/share/'
else:
    STATIC_URL = '/static/'
    MEDIA_URL = '/share/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
    'static/',
]

MEDIA_ROOT = os.path.join(BASE_DIR, 'share/')
