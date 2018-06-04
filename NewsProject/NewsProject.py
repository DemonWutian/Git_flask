from flask_script import Manager
from app import creat_app
from config import DevelopConfig
from super_command import CreateAdminCommand, RegisterUserCommand, HourLogin

app = creat_app(DevelopConfig)
manager = Manager(app)

from models import db
db.init_app(app)

from flask_migrate import Migrate, MigrateCommand
Migrate(app, db)
manager.add_command("db", MigrateCommand)
manager.add_command("createadmin", CreateAdminCommand)
manager.add_command("registeruser", RegisterUserCommand)
manager.add_command("hourlogin", HourLogin)

if __name__ == '__main__':
    # print(app.url_map)
    manager.run()
