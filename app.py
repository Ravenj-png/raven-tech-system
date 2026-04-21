import os, json, sqlite3
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHash
import jwt
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["*"])
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["100 per hour"])

# Config
SECRET_KEY = os.getenv("FLASK_SECRET", "dev-secret-change-in-prod")
TOKEN_EXPIRES = int(os.getenv("JWT_EXPIRES_HOURS", 7))
DATABASE = os.getenv("DATABASE", "schoolhub.db")

# 🔐 Argon2id (auto-salts & embeds salt in hash)
ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1, hash_len=32, salt_len=16)

# DB Helpers
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.teardown_appcontext
def close_db(ex):
    db = g.pop('db', None)
    if db: db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL CHECK(role IN ('admin','dos','teacher','classTeacher','student')),
                email TEXT, phone TEXT, password_hash TEXT NOT NULL, name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP, UNIQUE(email), UNIQUE(phone)
            );
            CREATE TABLE IF NOT EXISTS students (                id INTEGER PRIMARY KEY, name TEXT NOT NULL, phone TEXT, class TEXT,
                combination TEXT DEFAULT '', is_candidate INTEGER DEFAULT 0,
                subjects TEXT DEFAULT '[]', subsidiaries TEXT DEFAULT '[]',
                join_date TEXT, image TEXT DEFAULT '', results TEXT DEFAULT '[]',
                reports TEXT DEFAULT '[]', alerts TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT CHECK(type IN ('teacher','classTeacher')),
                name TEXT NOT NULL, subjects TEXT DEFAULT '[]', assigned_class TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT,
                target TEXT DEFAULT 'all', created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        db.commit()

# JWT
def make_token(user):
    return jwt.encode({
        "user_id": user["id"], "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRES),
        "iat": datetime.now(timezone.utc)
    }, SECRET_KEY, algorithm="HS256")

def token_required(f):
    def wrapper(*a, **k):
        tok = request.headers.get("Authorization")
        if not tok or not tok.startswith("Bearer "): return jsonify({"error": "Missing token"}), 401
        try:
            g.user = jwt.decode(tok.split(" ")[1], SECRET_KEY, algorithms=["HS256"])
        except: return jsonify({"error": "Invalid token"}), 401
        return f(*a, **k)
    wrapper.__name__ = f.__name__
    return wrapper

# 🔑 Login Route (Argon2 Verification)
@app.route("/api/login", methods=["POST"])
@limiter.limit("20 per minute")
def login():
    d = request.get_json()
    role, ident, pwd = d.get("role"), d.get("identifier"), d.get("password")
    if not all([role, ident, pwd]): return jsonify({"error": "Missing fields"}), 400

    db = get_db()
    q = "SELECT id, role, name, phone, email, password_hash FROM users WHERE {} = ? AND role = ?"
    col = "phone" if role == "student" else "email"
    user = db.execute(q.format(col), (ident, role)).fetchone()
    if not user: return jsonify({"error": "Invalid credentials"}), 401
    try:
        if ph.verify(user["password_hash"], pwd):
            return jsonify({"token": make_token(user), "user": {"id": user["id"], "role": user["role"], "name": user["name"]}})
    except: pass
    return jsonify({"error": "Invalid credentials"}), 401

# 📥 Sync Route (Frontend calls this on login to pull fresh data)
@app.route("/api/sync", methods=["GET"])
@token_required
def sync():
    db = get_db()
    return jsonify({
        "students": [dict(r) for r in db.execute("SELECT * FROM students").fetchall()],
        "staff": [dict(r) for r in db.execute("SELECT * FROM staff").fetchall()],
        "announcements": [dict(r) for r in db.execute("SELECT * FROM announcements ORDER BY created_at DESC").fetchall()]
    })

# 📝 Add Student Route
@app.route("/api/students", methods=["POST"])
@token_required
def add_student():
    d = request.get_json()
    db = get_db()
    try:
        db.execute("INSERT INTO students (id, name, phone, class, combination, is_candidate, subjects, subsidiaries, join_date, image) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (d["id"], d["name"], d["phone"], d["class"], d.get("combination",""), d.get("isCandidate",0),
             json.dumps(d.get("subjects",[])), json.dumps(d.get("subsidiaries",[])), d.get("joinDate",""), d.get("image","")))
        db.commit()
        return jsonify({"message": "Saved"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# 🌱 Seed Default Accounts (Run once)
@app.route("/api/seed", methods=["POST"])
def seed():
    db = get_db()
    roles = {"admin": "admin@school.com", "dos": "dos@school.com", "teacher": "teacher@school.com", "classTeacher": "ct@school.com"}
    for role, email in roles.items():
        if not db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
            db.execute("INSERT INTO users (role, email, password_hash, name) VALUES (?,?,?,?)",
                (role, email, ph.hash("admin123" if role=="admin" else "password123"), role.capitalize()))
    db.commit()
    return jsonify({"message": "Seeded"})

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)