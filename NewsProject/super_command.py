import random

from flask import current_app
from flask_script import Command
from models import UserInfo, db
from datetime import datetime

class CreateAdminCommand(Command):
    def run(self):
        # 接受用户的账号密码
        mobile = input("请输入账号:")
        pwd = input("请输入密码:")

        # 判断用户是否已经存在
        user_count = UserInfo.query.filter_by(mobile=mobile).count()
        if user_count > 0:
            print("用户已经存在")
        else:
            user = UserInfo()
            user.mobile = mobile
            user.password = pwd
            user.isAdmin = True

            # 提交数据库
            db.session.add(user)
            db.session.commit()
            print("管理员账户添加成功!")


class RegisterUserCommand(Command):
    def run(self):
        # now = datetime.now()
        user_list = []
        for i in range(1500):
            user = UserInfo()
            user.mobile = str(i)
            user.nick_name = str(i)
            user.create_time = datetime(2018, random.randint(1,6), random.randint(1,28))
            user_list.append(user)
        db.session.add_all(user_list)
        db.session.commit()


class HourLogin(Command):
    def run(self):
        now = datetime.now()
        key = "login%d_%d_%d"%(now.year, now.month, now.day)
        for i in range(8, 20):
            current_app.redis_client.hset(key, "%02d:15"%i, random.randint(100, 2000))