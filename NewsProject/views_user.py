from flask import Blueprint, jsonify
from flask import current_app
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from models import db, UserInfo

user_blueprint = Blueprint("user", __name__, url_prefix="/user")


@user_blueprint.route('/image_yzm')
def image_yzm():
    from utils.captcha.captcha import captcha
    # name 表示一个随机的名称
    # yzm表示验证码字符串
    # buffer表示文件的二进制数据
    name, yzm, buffer = captcha.generate_captcha()

    # 验证码存入session中, 用于对比
    session["image_yzm"] = yzm

    response = make_response(buffer)
    # 默认返回的内容会被当做text/html解析, 告诉浏览器解释为图片
    response.mimetype = "image/png"

    return response


@user_blueprint.route('/sms_yzm')
def sms_yzm():
    # 调用短信验证码需要获取手机号, 在此之前需要先验证图片验证码
    dict1 = request.args
    mobile = dict1.get("mobile")
    image_yzm = dict1.get("image_yzm")

    # 对比图片验证码
    if image_yzm != session["image_yzm"]:
        return jsonify(result=1)

    # 随机生成数字4位
    import random
    yzm = random.randint(1000, 9999)

    # 保存到session, 方便以后对比
    session["sms_yzm"] = yzm

    from utils.ytx_sdk import ytx_send
    # ytx_send.sendTemplateSMS(mobile, {yzm, 5}, 1)
    print(yzm)

    return jsonify(result=2)


# 使用post方式接收数据, 对数据产生了修改
@user_blueprint.route('/register', methods=["POST"])
def register():
    # 接收数据
    dict1 = request.form
    mobile = dict1.get("mobile")
    image_yzm = dict1.get("image_yzm")
    sms_yzm = dict1.get("sms_yzm")
    pwd = dict1.get("pwd")

    # 验证数据有效性
    # 判断所有数据是否存在
    if not all([mobile, image_yzm, sms_yzm, pwd]):
        return jsonify(result=1)

    # 判断图片验证码是否正确
    if image_yzm != session["image_yzm"]:
        return jsonify(result=2)

    # 判断短信验证码是否正确
    # 接收到的字典中所有数据皆为字符串, 短信验证码如果要对比需要转换成int
    if int(sms_yzm) != session["sms_yzm"]:
        return jsonify(result=3)

    # 判断密码是否符合规定
    import re
    if not re.match(r"[a-zA-Z0-9_]{6,20}", pwd):
        return jsonify(result=4)

    # 判断手机号是否存在
    # 从数据库中查询数据, 如果查到则存在
    mobile_count = UserInfo.query.filter_by(mobile=mobile).count()
    if mobile_count > 0:
        return jsonify(result=5)

    # 创建对象
    user = UserInfo()
    user.nick_name = mobile
    user.mobile = mobile
    user.password = pwd

    # 保存并提交
    try:
        db.session.add(user)
        db.session.commit()
    except:
        current_app.logger_xjzx.error("注册用户时数据库访问失败")
        return jsonify(result=6)

    return jsonify(result=7)


@user_blueprint.route('/login', methods=["POST"])
def login():
    # 接收数据
    dict1 = request.form
    mobile = dict1.get("mobile")
    pwd = dict1.get("pwd")

    # 验证数据
    if not all([mobile, pwd]):
        return jsonify(result=1)

    # 从数据库中查询数据
    user = UserInfo.query.filter_by(mobile=mobile).first()

    # 如果user存在则返回对象, 不存在返回none
    if user:
        # 判断密码是否正确
        if user.check_pwd(pwd):
            # 正确
            session["user_id"] = user.id
            return jsonify(result=3, avatar=user.avatar, nick_name=user.nick_name)
        else:
            # 错误
            return jsonify(result=4)
    else:
        # 提示mobile错误
        return jsonify(result=2)


@user_blueprint.route('/logout', methods=["POST"])
def logout():
    session.pop("user_id")
    return jsonify(result=1)


import functools


# 定义验证登陆的装饰器
def login_required(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/")
        return func(*args, **kwargs)

    return inner


@user_blueprint.route('/')
@login_required
def index():
    # 从session中获取用户编号
    user_id = session["user_id"]

    # 查询用户对象传递到模板中使用
    user = UserInfo.query.get(user_id)

    return render_template(
        "news/user.html",
        user=user,
        title="用户中心"
    )


@user_blueprint.route('/base', methods=["POST", "GET"])
@login_required
def base():
    # 获取用户id
    user_id = session["user_id"]
    # 查询用户记录
    user = UserInfo.query.get(user_id)

    if request.method == "GET":
        return render_template("news/user_base_info.html", user=user)
    elif request.method == "POST":
        # 获取页面数据
        dict1 = request.form
        signature = dict1.get("signature")
        nick_name = dict1.get("nick_name")
        gender = dict1.get("gender")

        # 修改数据
        user.signature = signature
        user.nick_name = nick_name
        # 布尔类型需要转换
        user.gender = bool(gender)
        # 提交数据
        try:
            db.session.commit()
        except:
            # 记录错误信息到日志
            current_app.logger_xjzx.error("修改用户基本信息连接数据库失败")
            return jsonify(result=2)
        return jsonify(result=1)


@user_blueprint.route('/pic', methods=["GET", "POST"])
@login_required
def pic():
    user_id = session["user_id"]
    user = UserInfo.query.get(user_id)

    if request.method == "GET":
        return render_template("news/user_pic_info.html",user=user)
    elif request.method == "POST":
        # 接收文件
        f1 = request.files.get("avatar")

        # 保存文件到七牛云
        from utils.qiniu_xjzx import upload_pic
        f1_name = upload_pic(f1)

        # 保存文件到数据库
        user.avatar = f1_name

        # 提交
        db.session.commit()

        return jsonify(result=1, avatar_url=user.avatar_url)


@user_blueprint.route('/follow')
@login_required
def follow():
    return render_template("news/user_follow.html")


@user_blueprint.route('/pwd')
@login_required
def pwd():
    return render_template("news/user_pass_info.html")


@user_blueprint.route('/collect')
@login_required
def collect():
    return render_template("news/user_collection.html")


@user_blueprint.route('/release')
@login_required
def release():
    return render_template("news/user_news_release.html")


@user_blueprint.route('/newslist')
@login_required
def newslist():
    return render_template("news/user_news_list.html")
