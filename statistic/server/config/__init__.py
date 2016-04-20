import pytz

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    """Base configuration."""
    SECRET_KEY = 'my_precious'
    DEBUG = False
    BCRYPT_LOG_ROUNDS = 13
    WTF_CSRF_ENABLED = True
    DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    #BCRYPT_LOG_ROUNDS = 4
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/statistic'
    DEBUG_TB_ENABLED = True


class TestingConfig(BaseConfig):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    #BCRYPT_LOG_ROUNDS = 4
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = ''
    DEBUG_TB_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class ProductionConfig(BaseConfig):
    """Production configuration."""
    SECRET_KEY = 'my_precious'
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = ''
    DEBUG_TB_ENABLED = False

PARTNER_DEFAULT_TZ = pytz.timezone('Asia/Shanghai')

LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'simple': {'format': '%(asctime)s %(levelname)s: %(message)s'},
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(processName)s(%(process)d) %(threadName)s(%(thread)d): %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'statistic.server': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/hi/logs/statistic/statistic.log',
            'formatter': 'verbose',
            'backupCount': 30,
            'when': 'D'
        },
    },
    'loggers': {
        'statistic.server': {
            'handlers': ['statistic.server'],
            'level': 'INFO',
        },
    }
}
