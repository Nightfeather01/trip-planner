import os
# spl & docker customize config
DOCKER = 0
SPL = 0
# basic config
APPLICATION_ROOT_CONFIG = '/hanproj'
STATIC_FOLDER_CONFIG = 'static'
PREFERRED_URL_SCHEME = 'http'
# database config
HOSTNAME = 'localhost'
PORT = '3306'
DATABASE = 'trip_planner'
USERNAME = 'root'
PASSWORD = '920525'
if SPL:
    PASSWORD = '1234'
DB_URL = 'mysql://{}:{}@{}:{}/{}'.format(USERNAME, PASSWORD, HOSTNAME, PORT, DATABASE)
if DOCKER:
    PASSWORD = 'itlab13579'
    DB_URL = 'mysql://{}:{}@mariadb/{}'.format(USERNAME, PASSWORD, DATABASE)
SQLALCHEMY_DATABASE_URI = DB_URL
# googleAPI config
API_KEY = 'your-google-api-key'
NEARBY_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?'
DETAIL_URL = 'https://maps.googleapis.com/maps/api/place/details/json?'
DIRECTIONS_URL = 'https://maps.googleapis.com/maps/api/directions/json?'
# booking config
BOOKING_API_KEY = 'your-booking-api-key'


class Config:
    SECRET_KEY = 'YouWillNeverGuess'
    APPLICATION_ROOT = APPLICATION_ROOT_CONFIG

    # 靜態文件路徑配置
    STATIC_FOLDER = STATIC_FOLDER_CONFIG

    # 其他配置保持不變
    SQLALCHEMY_DATABASE_URI = DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # 若使用 MySQL，建議添加以下配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,  # 連接池回收時間
        'pool_timeout': 20,  # 連接池超時時間
        'pool_size': 5,  # 連接池大小
        'max_overflow': 10  # 最大溢出連接數
    }

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = DB_URL


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or DB_URL


# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
