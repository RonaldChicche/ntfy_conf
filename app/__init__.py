from flask import Flask
from flask_sqlalchemy import SQLAlchemy
#from flask_socketio import SocketIO
from flask_migrate import Migrate
from dotenv import load_dotenv
from app.utils import insertar_prioridades

import os


db = SQLAlchemy()
#socketio = SocketIO(cors_allowed_origins="*")
migrate = Migrate()


def create_app():
    load_dotenv()  # Carga variables del .env

    app = Flask(__name__)
    app.secret_key = "clave_segura"  #os.getenv('SECRET_KEY')
    app.config.from_object('app.config.Config')

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes import register_routes
    register_routes(app)

    with app.app_context():
        db.create_all()  # Crea las tablas si no existen
        insertar_prioridades()

    return app
