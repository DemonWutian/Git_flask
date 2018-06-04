from flask import Blueprint
from flask import abort
from flask import current_app
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from datetime import datetime

from models import UserInfo, NewsInfo

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
    user_month = UserInfo.query.filter_by(isAdmin=False).filter(UserInfo.create_time>=month_first).count()
    # 日新增数
    day_first = datetime(now.year, now.month, now.day)
    user_day = UserInfo.query.filter_by(isAdmin=False).filter(UserInfo.create_time>=day_first).count()
    # 时间段对应的登录数
    key = "login%d_%d_%d"%(now.year, now.month, now.day)
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
    pagination = UserInfo.query.filter(UserInfo.isAdmin==False).\
        order_by(UserInfo.id.desc()).\
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
    #接收数据
    page = int(request.args.get("page", "1"))
    pagination = NewsInfo.query.order_by(NewsInfo.id).paginate(page, 10, False)
    news_list = pagination.items
    total_page = pagination.pages
    return render_template(
        "admin/news_review.html",
        page=page,
        total_page=total_page,
        news_list=news_list
    )


@admin_blueprint.route('/news_edit')
def news_edit():
    return render_template("admin/news_edit.html")


@admin_blueprint.route('/news_type')
def news_type():
    return render_template("admin/news_type.html")
