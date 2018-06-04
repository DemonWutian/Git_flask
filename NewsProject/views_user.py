from flask import Blueprint, jsonify
from flask import current_app
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from models import db, UserInfo, NewsInfo, NewsCategory
from datetime import datetime

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


def login_hour_count():
    now = datetime.now()
    login_key = "login%d_%d_%d" % (now.year, now.month, now.day)
    login_prop = ['08:15', '09:15', '10:15', '11:15', '12:15', '13:15', '14:15', '15:15', '16:15', '17:15', '18:15',
                  '19:15']
    for index, item in enumerate(login_prop):
        if now.hour < index + 8 or (now.hour == index + 8 and now.minute <= 15):
            count = int(current_app.redis_client.hget(login_key, item))
            count += 1
            current_app.redis_client.hset(login_key, item, count)
    else:
        count = int(current_app.redis_client.hget(login_key, "19:15"))
        count += 1
        current_app.redis_client.hset(login_key, "19:15", count)

        # if now.hour < 8 or (now.hour==8 and now.minute<=15):
        #     count = int(current_app.redis_client.hget(login_key, "08:15"))
        #     count += 1
        #     current_app.redis_client.hset(login_key, "08:15", count)


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
            # 统计每小时登陆次数
            login_hour_count()
            # 正确, 状态保持
            session["user_id"] = user.id

            return jsonify(result=3, avatar_url=user.avatar_url, nick_name=user.nick_name)
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
        if gender == "True":
            gender = True
        else:
            gender = False
        user.gender = gender  # True if gender=="True" else False
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
        return render_template("news/user_pic_info.html", user=user)
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
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)

    # 接收页码值参数
    page = int(request.args.get('page', '1'))
    # 分页
    pagination = user.follow_user.paginate(page, 4, False)
    # 获取当前页数据
    user_list = pagination.items
    # 总页数
    total_page = pagination.pages

    return render_template(
        'news/user_follow.html',
        user_list=user_list,
        total_page=total_page,
        page=page
    )


@user_blueprint.route('/pwd', methods=["POST", "GET"])
@login_required
def pwd():
    user_id = session["user_id"]
    user = UserInfo.query.get(user_id)
    if request.method == "GET":
        return render_template("news/user_pass_info.html")
    elif request.method == "POST":
        # 接收数据
        dict1 = request.form
        current_pwd = dict1.get("current_pwd")
        new_pwd = dict1.get("new_pwd")
        new_pwd2 = dict1.get("new_pwd2")
        # 判断数据格式和正确性
        if not all([current_pwd, new_pwd, new_pwd2]):
            msg = "密码不能为空"
            return render_template(
                "news/user_pass_info.html",
                msg=msg
            )
        # 判断密码是否符合规定
        import re
        if not re.match(r"[a-zA-Z0-9_]{6,20}", current_pwd):
            msg = "旧密码输入有误"
            return render_template(
                "news/user_pass_info.html",
                msg=msg
            )
        if not re.match(r"[a-zA-Z0-9_]{6,20}", new_pwd):
            msg = "新密码格式有误, 6-20大小写字母, 0-9数字以及下划线'_'"
            return render_template(
                "news/user_pass_info.html",
                msg=msg
            )
        # 判断旧密码和新密码是否一致
        if current_pwd == new_pwd:
            msg = "新密码不能和旧密码重复哦!"
            return render_template(
                "news/user_pass_info.html",
                msg=msg
            )
        # 判断两次输入是否一样
        if new_pwd != new_pwd2:
            msg = "两次输入不一致"
            return render_template(
                "news/user_pass_info.html",
                msg=msg
            )
        # 判断旧密码是否和数据库中一样
        if not user.check_pwd(current_pwd):
            msg = "旧密码错误!"
            return render_template(
                "news/user_pass_info.html",
                msg=msg
            )
        # 所有输入都无误
        user.password = new_pwd
        # 提交数据库
        db.session.commit()
        # 响应
        return render_template(
            "news/user_pass_info.html",
            msg="密码修改成功"
        )


@user_blueprint.route('/collect')
@login_required
def collect():
    # 查询数据库
    user_id = session["user_id"]
    user = UserInfo.query.get(user_id)
    # 从模板接收页码
    page = int(request.args.get("page", "1"))
    # 分页
    pagination = user.news_collect.paginate(page, 6, False)
    # 获取当前页数据
    newslist = pagination.items
    # 总页码
    total_page = pagination.pages
    return render_template(
        "news/user_collection.html",
        page=page,
        newslist=newslist,
        total_page=total_page
    )


@user_blueprint.route('/release', methods=['GET', 'POST'])
@login_required
def release():
    # 查询所有的分类，供编辑人员选择
    category_list = NewsCategory.query.all()
    # 接收新闻的编号
    news_id = request.args.get('news_id')

    if request.method == 'GET':
        if news_id is None:
            # 展示页面
            return render_template(
                'news/user_news_release.html',
                category_list=category_list,
                news=None
            )
        else:
            # 如果有新闻编号则进行修改，所以需要查询展示
            news = NewsInfo.query.get(int(news_id))
            return render_template(
                'news/user_news_release.html',
                category_list=category_list,
                news=news
            )
    elif request.method == 'POST':
        # 新闻的添加处理
        # 1.接收请求
        dict1 = request.form
        title = dict1.get('title')
        category_id = dict1.get('category')
        summary = dict1.get('summary')
        content = dict1.get('content')
        # 接收新闻图片
        news_pic = request.files.get('news_pic')

        if news_id is None:
            # 2.验证
            # 2.1.验证数据不为空
            if not all([title, category_id, summary, content, news_pic]):
                return render_template(
                    'news/user_news_release.html',
                    category_list=category_list,
                    msg='请将数据填写完整'
                )
        else:
            if not all([title, category_id, summary, content]):
                return render_template(
                    'news/user_news_release.html',
                    category_list=category_list,
                    msg='请将数据填写完整'
                )

        # 上传图片(需要在添加之前上传, 才能得到图片地址)
        if news_pic:
            from utils.qiniu_xjzx import upload_pic
            filename = upload_pic(news_pic)

        # 3.添加
        if news_id is None:
            news = NewsInfo()
        else:
            news = NewsInfo.query.get(news_id)
        news.category_id = int(category_id)

        if news_pic:
            news.pic = filename

        news.title = title
        news.summary = summary
        news.content = content
        news.status = 1
        news.update_time = datetime.now()
        news.user_id = session['user_id']

        # 4.提交到数据库
        db.session.add(news)
        db.session.commit()

        # 5.响应：转到列表页
        return redirect('/user/newslist')


@user_blueprint.route('/newslist')
@login_required
def newslist():
    # 查询数据库
    user_id = session["user_id"]
    user = UserInfo.query.get(user_id)

    # 获取页码
    page = int(request.args.get("page", "1"))
    # 查询所有用户收藏的新闻
    pagination = user.news.order_by(NewsInfo.update_time.desc()).paginate(page, 6, False)
    newslist = pagination.items
    total_page = pagination.pages
    return render_template(
        "news/user_news_list.html",
        page=page,
        newslist=newslist,
        total_page=total_page
    )
