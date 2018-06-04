# coding=utf-8
from flask import Flask
from flask import render_template
from flask_wtf.csrf import CSRFProtect
from flask_session import Session


def creat_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    CSRFProtect(app)

    # 使用session初始化
    Session(app)


    # 注册蓝图
    from views_user import user_blueprint
    from views_admin import admin_blueprint
    from views_news import news_blueprint

    app.register_blueprint(user_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(news_blueprint)

    # 引入python自带的日志包
    import logging
    from logging.handlers import RotatingFileHandler
    # 设置日志的记录等级
    logging.basicConfig(level=logging.DEBUG)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler(config.BASE_DIR + "/logs/xjzx.log", maxBytes=1024 * 1024 * 100,
                                           backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)
    app.logger_xjzx = logging

    # 从config中读取session配置
    host = app.config.get("REDIS_HOST")
    port = app.config.get("REDIS_PORT")
    db = app.config.get("REDIS_DB")

    # 将用户对评论的回复存储到redis中
    import redis
    app.redis_client = redis.StrictRedis(host=host, port=port, db=db)

    @app.errorhandler(404)
    def not_found_errot(e):
        return render_template("news/404.html")

    return app




