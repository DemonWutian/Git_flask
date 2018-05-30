import redis
import os


class Config(object):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@localhost:3306/xjzx9"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # redis配置
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB =9
    # session
    SECRET_KEY = "itheima"
    # flask_session的配置信息
    SESSION_TYPE = "redis"  # 指定session保存到redis中
    SESSION_USE_SIGNER = True  # 让cookie中的session_id被加密签名处理
    # 使用redis的实例
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    PERMANENT_SESSION_LIFETIME = 60*60*24*14  # session的有效期

    # __file__ --> config.py
    # os.path.abspath()-->/home/python/Desktop/Wutian_flask/NewsProject/config.py
    # os.path.dirname()-->/home/python/Desktop/Wutian_flask/NewsProject
    # 表示项目所在目录
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # 七牛云配置
    QINIU_AK = "H999S3riCJGPiJOity1GsyWufw3IyoMB6goojo5e"
    QINIU_SK = "uOZfRdFtljIw7b8jr6iTG-cC6wY_-N19466PXUAb"
    QINIU_BUCKET = "itcast20171104"
    QINIU_URL = "http://oyvzbpqij.bkt.clouddn.com/"


class DevelopConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@localhost:3306/xjzx9"
