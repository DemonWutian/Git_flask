from flask import Blueprint
from flask import render_template

# 不加前缀, 用户可直接访问

news_blueprint = Blueprint("news", __name__)

# 新闻首页视图
@news_blueprint.route('/')
def index():
    return render_template("news/index.html")

