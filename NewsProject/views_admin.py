from flask import Blueprint, jsonify
from flask import abort
from flask import current_app
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from datetime import datetime

from models import UserInfo, NewsInfo, db, NewsCategory
from utils.qiniu_xjzx import upload_pic

admin_blueprint = Blueprint("admin", __name__, url_prefix="/admin")


@admin_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template("admin/login.html")
    elif request.method == "POST":
        # 接收数据
        dict1 = request.form
        mobile = dict1.get("username")
        pwd = dict1.get("password")

        # 验证完整性
        if not all([mobile, pwd]):
            abort(404)
        # 验证密码
        user = UserInfo.query.filter_by(isAdmin=True, mobile=mobile).first()
        if user is None:
            return render_template(
                "admin/login.html",
                mobile=mobile,
                pwd=pwd,
                msg="用户不存在"
            )
        if not user.check_pwd(pwd):
            return render_template(
                "admin/login.html",
                mobile=mobile,
                pwd=pwd,
                msg="密码错误"
            )
        session["admin_user_id"] = user.id
        return redirect("/admin/")


@admin_blueprint.before_request
def before_request():
    if request.path != "/admin/login":
        if "admin_user_id" not in session:
            return redirect("/admin/login")
        # g变量一般配合钩子函数使用, 创建的变量是全局变量, 可以在视图或模板中调用
        g.user = UserInfo.query.get(session["admin_user_id"])


@admin_blueprint.route('/')
def index():
    if "admin_user_id" in session:
        user = UserInfo.query.get(session["admin_user_id"])
        return render_template(
            "admin/index.html",
            user=user
        )
    else:
        return redirect("/admin/login")


@admin_blueprint.route('/logout')
def logout():
    del session["admin_user_id"]
    return redirect("/admin/login")


@admin_blueprint.route('/user_count')
def user_count():
    now = datetime.now()
    # 用户总数
    user_total = UserInfo.query.filter_by(isAdmin=False).count()
    # 月新增数
    month_first = datetime(now.year, now.month, 1)
    user_month = UserInfo.query.filter_by(isAdmin=False).filter(UserInfo.create_time >= month_first).count()
    # 日新增数
    day_first = datetime(now.year, now.month, now.day)
    user_day = UserInfo.query.filter_by(isAdmin=False).filter(UserInfo.create_time >= day_first).count()
    # 时间段对应的登录数
    key = "login%d_%d_%d" % (now.year, now.month, now.day)
    hour_list = current_app.redis_client.hkeys(key)
    hour_list = [hour.decode() for hour in hour_list]
    count_list = []
    for hour in hour_list:
        count = int(current_app.redis_client.hget(key, hour))
        count_list.append(count)
    return render_template(
        "admin/user_count.html",
        user_total=user_total,
        user_month=user_month,
        user_day=user_day,
        hour_list=hour_list,
        count_list=count_list
    )


@admin_blueprint.route('/user_list')
def user_list():
    dict1 = request.args
    page = int(dict1.get("page", "1"))
    pagination = UserInfo.query.filter(UserInfo.isAdmin == False). \
        order_by(UserInfo.id.desc()). \
        paginate(page, 9, False)
    total_page = pagination.pages
    user_list1 = pagination.items
    return render_template(
        "admin/user_list.html",
        page=page,
        total_page=total_page,
        user_list1=user_list1
    )


@admin_blueprint.route('/news_review')
def news_review():
    return render_template(
        "admin/news_review.html",
    )


@admin_blueprint.route('/news_review_json')
def news_review_json():
    # 接收数据
    page = int(request.args.get("page", "1"))
    input_txt = request.args.get("input_txt")
    pagination = NewsInfo.query
    if input_txt:
        pagination = pagination.filter(NewsInfo.title.contains(input_txt))
    pagination = pagination.order_by(NewsInfo.id.desc()).paginate(page, 10, False)
    news_list1 = pagination.items
    total_page = pagination.pages
    news_list2 = []
    for news in news_list1:
        news_dict = {
            "id": news.id,
            "title": news.title,
            "create_time": news.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": news.status
        }
        news_list2.append(news_dict)
    return jsonify(
        total_page=total_page,
        news_list=news_list2
    )


@admin_blueprint.route('/news_review_detail/<int:news_id>', methods=["GET", "POST"])
def news_review_detail(news_id):
    # 接收数据, 查询
    news = NewsInfo.query.get(news_id)
    # get请求
    if request.method == "GET":
        return render_template(
            "admin/news_review_detail.html",
            news=news
        )
    elif request.method == "POST":
        # 接收数据action和拒绝reason
        action = request.form.get("action")
        reason = request.form.get("reason")
        if action == "accept":
            news.status = 2
        else:
            news.status = 3
            news.reason = reason
        # 提交数据
        db.session.commit()
        # 返回数据
        return redirect("/admin/news_review")


@admin_blueprint.route('/news_edit')
def news_edit():
    return render_template("admin/news_edit.html")


@admin_blueprint.route('/news_edit_json')
def news_edit_json():
    # 获取数据
    input_txt = request.args.get("input_txt")
    page = int(request.args.get("page", "1"))
    pagination = NewsInfo.query
    if input_txt:
        pagination = pagination.filter(NewsInfo.title.contains(input_txt))
    pagination = pagination.order_by(NewsInfo.id.desc()).paginate(page, 10, False)
    # 当前页数据
    news_list1 = pagination.items
    # 总页数
    total_page = pagination.pages
    news_list2 = []
    for news in news_list1:
        news_dict = {
            "id": news.id,
            "title": news.title,
            "create_time": news.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        news_list2.append(news_dict)
    # 返回json数据
    return jsonify(
        news_list=news_list2,
        total_page=total_page
    )


@admin_blueprint.route('/news_edit_detail/<int:news_id>', methods=['GET', 'POST'])
def news_edit_detail(news_id):
    news = NewsInfo.query.get(news_id)
    if request.method == "GET":
        category_list = NewsCategory.query.all()
        return render_template(
            "admin/news_edit_detail.html",
            news=news,
            category_list=category_list
        )
    elif request.method == "POST":
        # 接收数据
        dict1 = request.form
        title = dict1.get("title")
        category_id = dict1.get("category_id")
        summary = dict1.get("summary")
        pic = request.files.get("pic")
        content = dict1.get("content")
        # 保存数据到数据库
        if pic:
            pic_name = upload_pic(pic)
            news.pic = pic_name
        news.title = title
        news.category_id = int(category_id)
        news.summary = summary
        news.content = content
        # 提交
        db.session.commit()
        # 响应
        return redirect("/admin/news_edit")


@admin_blueprint.route('/news_type')
def news_type():
    return render_template("admin/news_type.html")


@admin_blueprint.route('/news_type_list')
def news_type_list():
    # 查询数据
    category_list1 = NewsCategory.query.all()
    category_list2 = []
    for category in category_list1:
        category_dict = {
            "id": category.id,
            "name": category.name
        }
        category_list2.append(category_dict)

    # 返回json数据
    return jsonify(category_list=category_list2)


@admin_blueprint.route('/news_type_edit', methods=['POST'])
def news_type_edit():
    # 接收数据
    cid = request.form.get("id")
    name = request.form.get("name")
    # 查询分类是否重复
    category_exist = NewsCategory.query.filter_by(name=name).count()
    if category_exist > 0:
        return jsonify(result=2)
    category = NewsCategory.query.get(cid)
    category.name = name
    # 保存到数据库
    db.session.commit()
    return jsonify(result=1)


@admin_blueprint.route('/news_type_add', methods=['POST'])
def news_type_add():
    # 接收数据
    name = request.form.get("name")
    # 查询是否重复
    category_exist = NewsCategory.query.filter_by(name=name).count()
    if category_exist > 0:
        return jsonify(result=2)
    category = NewsCategory()
    category.name = name
    # 提交
    db.session.add(category)
    db.session.commit()
    return jsonify(result=1)