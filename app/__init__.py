from flask import Flask
from flask_sqlalchemy import SQLAlchemy
#from flask_socketio import SocketIO
from flask_migrate import Migrate
from app.config import get_env, get_config_value
from app.utils import insertar_prioridades
#from app.routes.opc_routes import opc_client
#from app.opc_handler import OpcUaClient

import os


db = SQLAlchemy()
migrate = Migrate()


def create_app():

    app = Flask(__name__)
    app.secret_key = get_env('SECRET_KEY')
    app.config["SQLALCHEMY_DATABASE_URI"] = get_env("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes import register_routes
    register_routes(app)

    with app.app_context():
        db.create_all()  # Crea las tablas si no existen
        insertar_prioridades()


    return app
