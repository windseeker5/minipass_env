from flask import Flask
from models import db, Admin
import bcrypt
import os

# Compute absolute path to the DB file
db_path = os.path.abspath("instance/dev_database.db")

# Ensure folder exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    print("📂 Using DB:", db_path)

    email = "kdresdell@gmail.com"
    password = "admin123"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    admin = Admin.query.filter_by(email=email).first()
    if not admin:
        admin = Admin(email=email, password_hash=hashed)
        db.session.add(admin)
        print(f"✅ Created new admin: {email}")
    else:
        admin.password_hash = hashed
        print(f"✅ Updated password for existing admin: {email}")

    db.session.commit()
    print("🎉 Done. You can now log in.")
