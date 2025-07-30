import sqlite3
import bcrypt
import sys
import os

# Customize these as needed
db_path = "instance/dev_database.db"
email_to_check = "kdresdell@gmail.com"
input_password = sys.argv[1] if len(sys.argv) > 1 else "admin123"

# Absolute path resolution (optional)
db_path = os.path.abspath(db_path)

print(f"🔍 Checking password for: {email_to_check}")
print(f"📂 Database: {db_path}")
print(f"🔑 Password to test: {input_password}")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT password_hash FROM Admin WHERE email = ?", (email_to_check,))
row = cur.fetchone()

if not row:
    print("❌ Admin not found.")
    sys.exit(1)

stored_hash = row[0]
if isinstance(stored_hash, str):
    stored_hash = stored_hash.encode("utf-8")  # legacy TEXT
elif isinstance(stored_hash, memoryview):
    stored_hash = stored_hash.tobytes()        # BLOB

# Compare hash
if bcrypt.checkpw(input_password.encode(), stored_hash):
    print("✅ Password is valid!")
else:
    print("❌ Password is NOT valid.")
