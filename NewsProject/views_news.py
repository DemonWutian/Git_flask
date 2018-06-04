from flask import Blueprint, jsonify
from flask import abort
from flask import render_template
from flask import request
from flask import session

from models import db, NewsCategory, UserInfo, NewsInfo, NewsComment

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
        count_list=count_list,
        title="首页"
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


@news_blueprint.route('/<int:news_id>')
def detail(news_id):
    news = NewsInfo.query.get(news_id)
    # 判断请求地址是否有效, 无效则抛出404异常
    # 异常处理定义在app中, 带有装饰器的异常处理函数中
    if news is None:
        abort(404)

    # 右上角登陆状态判断
    if "user_id"in session:
        user = UserInfo.query.get(session["user_id"])
    else:
        user = None
    # 查询点击量排行, 并传递到模板
    # 点击量+1
    news.click_count += 1
    db.session.commit()
    # 查询点击排名前六的新闻列表
    count_list = NewsInfo.query.order_by(NewsInfo.click_count.desc())[0:6]

    # 传递对象到模板中
    return render_template(
        "news/detail.html",
        news=news,
        title="文章详情页",
        user=user,
        count_list=count_list
    )


@news_blueprint.route('/collect/<int:news_id>', methods=["POST"])
def collect(news_id):
    # 接收参数action: 收藏or取消收藏, 默认为1, 收藏
    action = int(request.form.get("action", "1"))

    # 获取当前新闻对象
    news = NewsInfo.query.get(news_id)
    # 如果没获取到, 则返回json数据,但是js不做处理
    if news is None:
        return jsonify(result=1)

    # 获取当前用户对象
    # 判断用户是否登陆
    if "user_id" not in session:
        return jsonify(result=2)
    user = UserInfo.query.get(session["user_id"])

    # 判断是收藏还是取消收藏
    if action == 1:
        # 判断当前新闻是否已经被用户收藏, 如果被收藏了,直接返回html不做处理
        if news in user.news_collect:
            return jsonify(result=4)
        # 添加收藏, 最终数据会被存储到tb_user_news中
        user.news_collect.append(news)
    else:
        # 取消收藏
        # 判断当前新闻是否已经被收藏, 没有收藏则不做处理, 直接返回html
        if news not in user.news_collect:
            return jsonify(result=4)
        # 如果已经被收藏, 则取消收藏, 从列表中删除数据
        user.news_collect.remove(news)

    # 提交
    db.session.commit()
    return jsonify(result=3)


@news_blueprint.route('/comment/add', methods=["POST"])
def comment_add():
    # 接收数据: 新闻编号, 评论内容
    dict1 = request.form
    news_id = dict1.get("news_id")
    msg = dict1.get("msg")
    # 验证数据完整性
    if not all([news_id, msg]):
        return jsonify(result=1)

    # 判断新闻是否存在
    news = NewsInfo.query.get(news_id)
    if news is None:
        return jsonify(result=2)

    # 判断用户是否登陆
    if "user_id" not in session:
        return jsonify(result=3)

    # 新闻对象的评论数+1
    news.comment_count += 1
    # 保存
    comment = NewsComment()
    comment.news_id = int(news_id)
    comment.user_id = session["user_id"]
    comment.msg = msg

    db.session.add(comment)
    db.session.commit()

    return jsonify(
        result=4,
        comment_count=news.comment_count
    )


@news_blueprint.route('/comment/list/<int:news_id>')
def commentlist(news_id):
    # 根据新闻id查询对应的评论
    comment_list = NewsComment.query.filter_by(news_id=news_id)\
        .order_by(NewsComment.like_count.desc(), NewsComment.id.desc())

    # 转换数据, 返回json格式的数据
    comment_list2 = []
    for comment in comment_list:
        comment_dict = {
            "id": comment.id,
            "like_count": comment.like_count,
            "msg": comment.msg,
            "create_time": comment.create_time,
            "avatar": comment.user.avatar_url,
            "nick_name": comment.user.nick_name
        }
        comment_list2.append(comment_dict)

    return jsonify(comment_list=comment_list2)


@news_blueprint.route('/other')
def other():
    return render_template("news/other.html")