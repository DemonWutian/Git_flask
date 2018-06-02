from flask import Blueprint, jsonify
from flask import render_template
from flask import request
from flask import session

from models import NewsCategory, UserInfo, NewsInfo

# 不加前缀, 用户可直接访问

news_blueprint = Blueprint("news", __name__)


# 新闻首页视图
@news_blueprint.route('/')
def index():
    # 查询分类, 用于展示
    category_list = NewsCategory.query.all()

    # 判断用户是否登陆
    if "user_id" in session:
        user = UserInfo.query.get(session["user_id"])
    else:
        user = None

    # 查询点击量最高的6条新闻
    count_list = NewsInfo.query.order_by(NewsInfo.click_count.desc())[0:6]

    return render_template(
        "news/index.html",
        category_list=category_list,
        user=user,
        count_list=count_list
    )


@news_blueprint.route('/newslist')
def newslist():
    # 接收页码值
    page = int(request.args.get("page", "1"))
    # 查询数据并分页
    pagination = NewsInfo.query

    # 接收指定分类的编号
    category_id = int(request.args.get("category_id", "0"))
    if category_id:
        pagination = pagination.filter_by(category_id=category_id)
    pagination = pagination.order_by(NewsInfo.update_time.desc()).paginate(page, 4, False)
    # 本页数据
    news_list = pagination.items
    # 不需要总页码值, 页面上不需要显示

    # NewsInfo型的对象js无法识别, 需要转换成json格式数据
    news_list2 = []
    for news in news_list:
        news_dict = {
            "id": news.id,
            "pic_url": news.pic_url,
            "title": news.title,
            "summary": news.summary,
            "user_id": news.user_id,
            "user_nick_name": news.user.nick_name,
            "update_time": news.update_time,
            "user_avatar": news.user.avatar_url,
            "category_id": news.category_id
        }
        news_list2.append(news_dict)
    return jsonify(
        page=page,
        news_list=news_list2
    )

