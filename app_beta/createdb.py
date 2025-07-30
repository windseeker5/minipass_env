from flask import Flask
from models import db
import os

app = Flask(__name__)

# ✅ Set absolute DB path
db_path = os.path.join(app.root_path, 'instance', 'dev_database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ✅ Ensure instance folder exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

print("Creating DB at:", db_path)
print("Instance folder exists:", os.path.exists(os.path.dirname(db_path)))

with app.app_context():
    db.create_all()
    print("✅ All tables created in dev_database.db")
