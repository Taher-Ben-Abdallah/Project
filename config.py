# to generate Secret keys for the application instance
import secrets
from datetime import timedelta

db_username = 'taher'
db_password = 'taher'


class Config(object):
    DEBUG = False
    TESTING = False

    MONGODB_HOST = f'mongodb+srv://{db_username}:{db_password}@cluster0.xz1n1yo.mongodb.net/?retryWrites=true&w=majority'

    #used for salting the verification tokens
    VERIFICATION_TOKEN_AGE = 3600
    VERIFICATION_TOKEN_SALT = 'a2aj*7Wj/AWrj4As'

    JWT_SECRET_KEY = secrets.token_urlsafe(20)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)

    #EMAIL_SERVICE_PARAMS

    #EMAIL_HOST = 'localhost'
    MAIL_DEFAULT_SENDER = "noreply@talan.com"
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_DEBUG = False
    EMAIL_USER = 'taherba23@gmail.com'
    EMAIL_PASSWORD = 'lpnoixuidsgnieuy'

    #FRONTEND
    FRONTEND_WEBSITE_URL = 'https://websiteurl.com'


    UPLOADS = ''


class ProductionConfig(Config):
    SECRET_KEY = secrets.token_urlsafe(22)


class DevelopmentConfig(Config):
    ENV = "development"
    DEBUG = True

    SECRET_KEY = secrets.token_urlsafe(10)


class TestingConfig(Config):
    TESTING = True

    SECRET_KEY = secrets.token_urlsafe(10)
