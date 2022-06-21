from flask import Flask
import os
from app.api import controllers
from .database import db
from flask_migrate import Migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(os.environ['APP_SETTINGS'])

    db.init_app(app)
    migrate = Migrate(app, db)
    with app.test_request_context():
        db.create_all()

    import app.api.controllers as shop_api
    app.register_blueprint(shop_api.api_module)

    return app
