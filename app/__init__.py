# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config
from .models import db
from datetime import timedelta

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from .routes import main
        app.register_blueprint(main)
    
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)

    return app






#ONAANGEPAST !!!