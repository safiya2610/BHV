import sqlite3

DB_NAME = "users.db"
ADMIN_EMAIL = "hellosafiya6@gmail.com".lower()

db = sqlite3.connect(DB_NAME)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL
)
""")

try:
    cur.execute("INSERT INTO admins (email) VALUES (?)", (ADMIN_EMAIL,))
    print("ADMIN CREATED")
except sqlite3.IntegrityError:
    print("ADMIN ALREADY EXISTS")

db.commit()
db.close()
