from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI
from datetime import datetime, timezone
from functools import wraps
import os, secrets, json

app = Flask(__name__)
CORS(app)

# ── Database config ──────────────────────────────────────────────
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "mistake_halflife.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = secrets.token_hex(32)

db = SQLAlchemy(app)

# ── Models ───────────────────────────────────────────────────────
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    entries = db.relationship("MistakeEntry", backref="user", lazy=True, cascade="all, delete-orphan")

class MistakeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.String(20), default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    details = db.relationship("MistakeDetail", backref="entry", lazy=True, cascade="all, delete-orphan")

class MistakeDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey("mistake_entry.id"), nullable=False)
    mistake_type = db.Column(db.String(100), nullable=False)
    count = db.Column(db.Integer, nullable=False, default=0)

# ── Simple token store (in-memory, resets on restart) ────────────
tokens = {}   # token_string -> user_id

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        uid = tokens.get(token)
        if not uid:
            return jsonify({"error": "Unauthorized"}), 401
        g.user_id = uid
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        uid = tokens.get(token)
        if not uid:
            return jsonify({"error": "Unauthorized"}), 401
        user = User.query.get(uid)
        if not user or not user.is_admin:
            return jsonify({"error": "Admin access required"}), 403
        g.user_id = uid
        return f(*args, **kwargs)
    return decorated

# ── Auth endpoints ───────────────────────────────────────────────
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409
    user = User(username=username, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Registered successfully"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401
    token = secrets.token_hex(32)
    tokens[token] = user.id
    return jsonify({
        "token": token,
        "username": user.username,
        "is_admin": user.is_admin
    })

@app.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    username = data.get("username", "").strip()
    new_password = data.get("new_password", "").strip()
    if not username or not new_password:
        return jsonify({"error": "Username and new password required"}), 400
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({"message": "Password updated"})

# ── Mistake CRUD ─────────────────────────────────────────────────
@app.route("/mistakes", methods=["POST"])
@require_auth
def add_mistakes():
    """Accepts { details: [{type, count}, ...] }"""
    data = request.json
    details = data.get("details", [])
    if not details:
        return jsonify({"error": "No mistake details provided"}), 400

    entry = MistakeEntry(user_id=g.user_id)
    db.session.add(entry)
    db.session.flush()  # get entry.id

    for d in details:
        mt = d.get("type", "").strip()
        ct = int(d.get("count", 0))
        if mt and ct >= 0:
            detail = MistakeDetail(entry_id=entry.id, mistake_type=mt, count=ct)
            db.session.add(detail)

    db.session.commit()
    return jsonify({"message": "Mistakes added", "entry_id": entry.id})

@app.route("/mistakes", methods=["GET"])
@require_auth
def get_mistakes():
    entries = MistakeEntry.query.filter_by(user_id=g.user_id).order_by(MistakeEntry.created_at).all()
    result = []
    for e in entries:
        details = [{"type": d.mistake_type, "count": d.count} for d in e.details]
        result.append({
            "id": e.id,
            "date": e.date,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "details": details,
            "total": sum(d.count for d in e.details)
        })
    return jsonify(result)

@app.route("/mistakes/<int:entry_id>", methods=["DELETE"])
@require_auth
def delete_mistake(entry_id):
    entry = MistakeEntry.query.filter_by(id=entry_id, user_id=g.user_id).first()
    if not entry:
        return jsonify({"error": "Entry not found"}), 404
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Deleted"})

@app.route("/mistakes", methods=["DELETE"])
@require_auth
def clear_mistakes():
    MistakeEntry.query.filter_by(user_id=g.user_id).delete()
    db.session.commit()
    return jsonify({"message": "All entries cleared"})

# ── Admin endpoints ──────────────────────────────────────────────
@app.route("/admin/users", methods=["GET"])
@require_admin
def admin_users():
    users = User.query.all()
    result = []
    for u in users:
        total_mistakes = 0
        for e in u.entries:
            total_mistakes += sum(d.count for d in e.details)
        result.append({
            "id": u.id,
            "username": u.username,
            "is_admin": u.is_admin,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "total_entries": len(u.entries),
            "total_mistakes": total_mistakes
        })
    return jsonify(result)

@app.route("/admin/user/<int:user_id>/mistakes", methods=["GET"])
@require_admin
def admin_user_mistakes(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    entries = MistakeEntry.query.filter_by(user_id=user_id).order_by(MistakeEntry.created_at).all()
    result = []
    for e in entries:
        details = [{"type": d.mistake_type, "count": d.count} for d in e.details]
        result.append({
            "id": e.id,
            "date": e.date,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "details": details,
            "total": sum(d.count for d in e.details)
        })
    return jsonify({"username": user.username, "entries": result})

# ── Study Assistant (OpenAI + Local Fallback) ────────────────────
API_KEY = os.environ.get("OPENAI_API_KEY", "")

def local_fallback_answer(question):
    """Smart local fallback when OpenAI API is unavailable."""
    q = question.lower().strip()
    responses = [
        # Grammar & Writing
        (["grammar", "grammer", "english", "writing", "essay", "sentence", "paragraph"],
         "To improve grammar: 1) Read extensively to internalize correct patterns. 2) Practice writing daily and review your work. 3) Use tools like Grammarly for instant feedback. 4) Study one grammar rule per day (subject-verb agreement, tenses, punctuation). Consistent practice is key!"),
        # Math
        (["math", "maths", "algebra", "calculus", "equation", "geometry", "trigonometry", "arithmetic"],
         "For math improvement: 1) Master the fundamentals before moving to advanced topics. 2) Practice 5-10 problems daily. 3) When you make a mistake, write out the correct solution step-by-step. 4) Use visual aids and diagrams. 5) Don't skip steps — show all your work."),
        # Formula
        (["formula", "formulas", "equation"],
         "To master formulas: 1) Write them out by hand repeatedly. 2) Understand what each variable represents — don't just memorize. 3) Practice applying them in different problem types. 4) Create a formula sheet and review it before practice sessions."),
        # Units & Conversion
        (["unit", "units", "conversion", "convert"],
         "For unit conversions: 1) Always write units alongside numbers in every step. 2) Use dimensional analysis (cancel units systematically). 3) Convert everything to SI units before calculating. 4) Double-check your final answer's units match what's expected."),
        # Logarithm
        (["log", "logarithm", "ln", "natural log"],
         "For logarithm mastery: 1) Memorize the key properties: log(ab)=log(a)+log(b), log(a/b)=log(a)-log(b), log(a^n)=n·log(a). 2) Always check if the problem uses ln (base e) or log (base 10). 3) Practice converting between exponential and logarithmic forms."),
        # Exponent
        (["exponent", "power", "exponential"],
         "For exponent skills: 1) Review the laws: a^m × a^n = a^(m+n), (a^m)^n = a^(mn), a^(-n) = 1/a^n. 2) Pay careful attention to negative exponents and signs. 3) In decay/growth problems, double-check whether the exponent should be positive or negative."),
        # Study tips
        (["study", "learn", "prepare", "exam", "test", "revision", "revise"],
         "Effective study strategies: 1) Use active recall — test yourself instead of re-reading. 2) Apply spaced repetition — review at increasing intervals. 3) Study in focused 25-minute blocks (Pomodoro technique). 4) Teach concepts to someone else. 5) Sleep well — memory consolidation happens during sleep!"),
        # Motivation
        (["motivat", "lazy", "focus", "concentrate", "distract", "procrastinat"],
         "To stay motivated: 1) Break large tasks into small, achievable goals. 2) Track your progress — this app shows your improvement! 3) Reward yourself after completing study sessions. 4) Remember your 'why' — visualize your goals. 5) Start with just 5 minutes; momentum builds naturally."),
        # Time management
        (["time", "schedule", "plan", "routine", "manage"],
         "Time management tips: 1) Create a daily schedule with specific study blocks. 2) Prioritize difficult subjects when your energy is highest. 3) Use the 2-minute rule: if it takes <2 min, do it now. 4) Eliminate distractions during study time. 5) Review your day each evening and plan tomorrow."),
        # Half-life / Physics
        (["half-life", "half life", "decay", "radioactive", "physics", "nuclear"],
         "Half-life concepts: 1) N(t) = N₀ × (1/2)^(t/t½) is the core formula. 2) After 1 half-life, 50% remains; after 2, 25%; after 3, 12.5%. 3) The decay constant λ = ln(2)/t½. 4) Practice identifying what each variable represents before plugging in numbers."),
        # Reduce / Improve mistakes
        (["reduce", "decrease", "fewer", "less", "improve", "better", "mistake", "error"],
         "To reduce mistakes: 1) Track your errors by type — you're already doing this! 2) Focus extra practice on your most frequent mistake type. 3) Before submitting work, do a systematic check for each error type. 4) Review mistakes immediately after making them. 5) Your mistake half-life data shows your improvement trajectory!"),
        # Programming
        (["code", "coding", "program", "python", "java", "javascript", "debug", "bug"],
         "For coding improvement: 1) Write code daily, even small programs. 2) Read error messages carefully — they tell you what's wrong. 3) Use debugging tools and print statements. 4) Study others' code on GitHub. 5) Break problems into smaller functions before coding."),
        # Science
        (["science", "chemistry", "biology", "experiment"],
         "For science mastery: 1) Focus on understanding concepts, not just memorizing facts. 2) Draw diagrams and flowcharts. 3) Connect new concepts to what you already know. 4) Practice explaining concepts in your own words. 5) Do practice problems and past papers."),
        # Help
        (["help", "what can you", "who are you", "hello", "hi"],
         "Hi! I'm your Study Assistant. I can help with: 📚 Study strategies & tips, 🧮 Math & science questions, ✍️ Grammar & writing advice, ⏰ Time management, 💪 Motivation & focus, 📊 Analyzing your mistake patterns. Just ask me anything!"),
    ]

    for keywords, answer in responses:
        if any(kw in q for kw in keywords):
            return answer

    # Default response
    return ("Great question! Here are some general tips: "
            "1) Break the topic into smaller parts and tackle them one at a time. "
            "2) Practice consistently — even 15 minutes daily makes a difference. "
            "3) Review your mistakes from this tracker to identify patterns. "
            "4) Don't hesitate to seek help from teachers, peers, or online resources. "
            "Keep tracking your progress — you're on the right path! 🚀")

@app.route("/chat", methods=["POST"])
@require_auth
def chat():
    data = request.json
    question = data.get("question", "")
    mistakes_context = data.get("mistakes", "")

    # Try OpenAI first (if API key is available)
    if API_KEY:
        try:
            client = OpenAI(api_key=API_KEY)
            system_prompt = (
                "You are an intelligent, friendly study assistant. "
                "You can answer ANY question the student asks — academic subjects, study tips, "
                "problem-solving strategies, motivation, time management, or general knowledge. "
                "If the student shares their mistake data, incorporate that context to give "
                "personalized advice. Keep answers helpful, concise (2-4 sentences unless more detail is needed), "
                "and encouraging."
            )
            user_prompt = ""
            if mistakes_context:
                user_prompt += f"Student's mistake data: {mistakes_context}\n\n"
            user_prompt += f"Student's question: {question}"

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            reply = response.choices[0].message.content
            return jsonify({"reply": reply})
        except Exception:
            pass  # Fall through to local fallback

    # Local fallback
    reply = local_fallback_answer(question)
    return jsonify({"reply": reply})

# ── Home ─────────────────────────────────────────────────────────
@app.route("/")
def home():
    return "Mistake Half-Life Backend is running!"

# ── Init DB + seed admin ─────────────────────────────────────────
def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created (admin / admin123)")

# Always init DB (works with both gunicorn and python app.py)
init_db()

if __name__ == "__main__":
    app.run(debug=True)