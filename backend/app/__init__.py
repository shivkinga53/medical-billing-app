import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
db = SQLAlchemy()


def create_app():
    """
    Creates the Flask application and initializes its configuration, database, commands, and routes.

    Returns:
        The created Flask application.
    """
    app = Flask(__name__)
    CORS(app)

    app.config["SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = "uploads"

    # Ensure the upload folder exists
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])

    db.init_app(app)

    with app.app_context():
        from . import routes
        from . import models

        # Creates all tables if they don't exist
        db.create_all()

        from .commands import db_cli

        app.register_blueprint(db_cli)

    return app
