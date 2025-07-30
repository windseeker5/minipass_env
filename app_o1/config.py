import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Config:
    SECRET_KEY = "your_secret_key"

    basedir = os.path.abspath(os.path.dirname(__file__))
    db_env = os.environ.get("FLASK_ENV", "dev").lower()

    if db_env == "prod":
        db_file = "prod_database.db"
    else:
        db_file = "dev_database.db"

    db_path = os.path.join(basedir, "instance", db_file)

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    @staticmethod
    def get_setting(app, key, default=None):
        ...
