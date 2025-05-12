from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

db = SQLAlchemy()

def create_app():
    load_dotenv()  # Carga variables del .env

    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()  # Crea las tablas si no existen

    return app
