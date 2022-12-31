import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_navigation import Navigation
from flask_login import LoginManager
from os import path

db = SQLAlchemy()
DB_NAME = "traffic.db"
UPLOAD_FOLDER = './uploads'
CLIP_FOLDER = './clips'
RECORDS_FOLDER = "./records"
SECRET_KEY = "The World is not Enough"


def create_database(app, drop=False):
    if drop:
        with app.app_context():
            print("droped database")
            db.drop_all()

    if not path.exists('application/' + DB_NAME):
        with app.app_context():
            db.create_all()
            print("created database")


def create_folders():
    if not os.path.exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)
    if not os.path.exists(CLIP_FOLDER):
        os.mkdir(CLIP_FOLDER)
    if not os.path.exists(RECORDS_FOLDER):
        os.mkdir(RECORDS_FOLDER)


def create_users():
    from .dal import add_user
    from .models import User
    from .seed import initial_users
    for item in initial_users:
        add_user(item['email'], item['pass'])


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['CLIP_FOLDER'] = UPLOAD_FOLDER
    app.config['RECORDS_FOLDER'] = UPLOAD_FOLDER

    # db codes
    db.init_app(app)

    from .models import User
    create_database(app, True)

    # register login models and intialize Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # folder codes
    create_folders()

    # register views
    from .view import view
    from .auth import auth
    from .video import video

    app.register_blueprint(view, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(video, url_prefix='/')

    # register menu items
    nav = Navigation(app)
    nav.Bar('top', [
        nav.Item('Home', 'view.home', html_attrs={'icon': 'house-door'}),
        nav.Item('Live', 'view.video', html_attrs={'icon': 'webcam'}),
        nav.Item('Analytics', 'view.analytics', html_attrs={'icon': 'bar-chart-line'}),
        nav.Item('Clips', 'view.clips', html_attrs={'icon': 'record'}),
        nav.Item('Settings', 'view.settings', html_attrs={'icon': 'gear'})
    ])

    return app
