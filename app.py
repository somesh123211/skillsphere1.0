# ============================================================
# IMPORTS
# ============================================================
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
import pymysql
import mysql.connector
import jwt
import os
import re
import json
import random
import base64
import uuid
import smtplib
from email.mime.text import MIMEText
import google.generativeai as genai
from db import get_db



from datetime import datetime, date, timedelta
import pytz

IST = pytz.timezone("Asia/Kolkata")

def today_ist():
    return datetime.now(IST).date()


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found in .env")

genai.configure(api_key=GOOGLE_API_KEY)

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DB"),
}

SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 465
SMTP_USER = "9da39b001@smtp-brevo.com"
SMTP_PASS = os.getenv("BREVO_SMTP_PASS")
FROM_EMAIL = "techpallotine@gmail.com"

if not SECRET_KEY:
    raise Exception("SECRET_KEY missing")
if not GOOGLE_API_KEY:
    raise Exception("GOOGLE_API_KEY missing")
if not SMTP_PASS:
    raise Exception("BREVO_SMTP_PASS missing")





# ============================================================
# FLASK SETUP
# ============================================================
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
CORS(app, supports_credentials=True)


CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = os.path.join("uploads", "profile_images")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ============================================================
# GOOGLE GEMINI SETUP
# ============================================================
genai.configure(api_key=GOOGLE_API_KEY)

# ============================================================
# DATABASE HELPER
# ============================================================

import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)



# ============================================================
# OTP CONFIG (IN-MEMORY)
# ============================================================
OTP_TTL_SECONDS = 5 * 60
MAX_ATTEMPTS = 3

otp_store = {}
forgot_otp_store = {}


def generate_otp():
    return f"{random.randint(100000, 999999):06d}"


def send_otp_email_only(email):
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS)


    otp_store[email.lower()] = {
        "otp": otp,
        "expires_at": expires_at,
        "attempts": 0
    }

    html = load_html_template(
        "otp_template.html",
        otp=otp,
        year = datetime.now().year

    )

    send_email_smtp(
        email,
        "Placement Portal Email Verification",
        html
    )

    print("OTP sent (testing only):", otp)


def verify_otp(email, entered):
    key = email.lower()

    if key not in otp_store:
        return False, "No OTP found"

    entry = otp_store[key]

    if datetime.utcnow() > entry["expires_at"]:

        del otp_store[key]
        return False, "OTP expired"

    if entry["attempts"] >= MAX_ATTEMPTS:
        del otp_store[key]
        return False, "Maximum attempts exceeded"

    entry["attempts"] += 1

    if str(entered).strip() == entry["otp"]:
        del otp_store[key]
        return True, "OTP verified"

    return False, "Invalid OTP"

# ============================================================
# SEND OTP
# ============================================================
@app.route("/send_otp", methods=["POST"])
def send_otp():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"success": False, "message": "Email required"}), 400

    send_otp_email_only(email)
    return jsonify({"success": True, "message": "OTP sent"}), 200

# ============================================================
# VERIFY OTP & SIGNUP
# ============================================================
@app.route("/verify_otp_and_signup", methods=["POST"])
def verify_otp_and_signup():
    conn = None
    cur = None
    try:
        data = request.get_json() or {}

        required = ["name", "uid", "branch", "year", "email", "password", "otp"]
        for field in required:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "message": f"{field} required"
                }), 400

        # 🔐 Verify OTP first (no DB yet)
        ok, msg = verify_otp(data["email"], data["otp"])
        if not ok:
            return jsonify({"success": False, "message": msg}), 400

        conn = get_db()
        conn.begin()
        cur = conn.cursor()

        # 🚫 Check existing user
        cur.execute(
            "SELECT id FROM students WHERE email=%s OR uid=%s",
            (data["email"], data["uid"])
        )

        if cur.fetchone():
            conn.rollback()
            return jsonify({
                "success": False,
                "message": "User already exists"
            }), 400

        hashed = generate_password_hash(data["password"])

        # 🧾 Insert user
        cur.execute(
            """
            INSERT INTO students (name, uid, branch, year, email, password)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (
                data["name"],
                data["uid"],
                data["branch"],
                data["year"],
                data["email"],
                hashed
            )
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Signup successful"
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        print("SIGNUP ERROR:", repr(e))
        return jsonify({
            "success": False,
            "message": "Signup failed"
        }), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ============================================================
# LOGIN
# ============================================================
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password required"}), 400

    conn = None
    cur = None
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT uid, name, email, branch, year, password FROM students WHERE email=%s",
            (data["email"],)
        )
        user = cur.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 401

        if not check_password_hash(user["password"], data["password"]):
            return jsonify({"error": "Invalid credentials"}), 401

        # 🔐 JWT now contains minimal required identity data
        token = jwt.encode(
            {
                "uid": user["uid"],
                "year": user["year"],
                "branch": user["branch"],
                "exp": datetime.utcnow() + timedelta(hours=12)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        return jsonify({
            "message": "Login successful",
            "token": token,
            "student": {
                "name": user["name"],
                "email": user["email"],
                "uid": user["uid"],
                "branch": user["branch"],
                "year": user["year"]
            }
        }), 200

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



# ============================================================
# JWT DECORATOR
# ============================================================
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        # 🔥 Allow CORS preflight
        if request.method == "OPTIONS":
            return jsonify({"success": True}), 200

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token missing"}), 401

        token = auth_header.replace("Bearer ", "")

        try:
            # 🔹 Decode JWT (signature + expiry verified)
            data = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=["HS256"]
            )

            # 🔹 Construct user object (same shape as DB user)
            user = {
                "uid": data["uid"],
                "year": data.get("year"),
                "branch": data.get("branch")
            }

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401

        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        except Exception as e:
            print("TOKEN ERROR:", repr(e))
            return jsonify({"error": "Authentication failed"}), 401

        return f(user, *args, **kwargs)

    return decorated



# ============================================================
# GEMINI QUESTION GENERATOR
# ============================================================



# ============================================================
# PROFILE
# ============================================================
@app.route("/get_student_profile", methods=["GET"])
@token_required
def get_student_profile(current_user):
    conn = None
    cur = None
    try:
        uid = current_user["uid"]
        year = int(current_user["year"])

        attempts_table = (
            "daily_quiz_attempts_y2"
            if year == 2
            else "daily_quiz_attempts_y3"
        )

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            SELECT COUNT(*) AS total_attempts
            FROM {attempts_table}
            WHERE uid=%s
            """,
            (uid,)
        )
        attempts = cur.fetchone()["total_attempts"]

        cur.execute(
            "SELECT name, branch, profile_image FROM students WHERE uid=%s",
            (uid,)
        )
        student = cur.fetchone()

        if not student:
            return jsonify({
                "success": False,
                "error": "Student not found"
            }), 404

        profile_image = student["profile_image"]
        if profile_image and not profile_image.startswith("http"):
            profile_image = request.host_url.rstrip("/") + "/" + profile_image

        return jsonify({
            "success": True,
            "profile": {
                "name": student["name"],
                "uid": uid,
                "branch": student["branch"],
                "year": year,
                "profile_image": profile_image,
                "aptitude_attempted": attempts,
                "branch_level": current_user.get("current_level", 1)
            }
        }), 200

    except Exception as e:
        print("❌ PROFILE ERROR:", repr(e))
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



@app.route("/upload_profile_image", methods=["POST", "OPTIONS"])
@token_required
def upload_profile_image(current_user):

    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    data = request.get_json(silent=True) or {}
    image_base64 = data.get("image_base64")

    if not image_base64:
        return jsonify({"error": "Image missing"}), 400

    # 🔒 Remove base64 header if present
    if "," in image_base64:
        image_base64 = image_base64.split(",")[1]

    # 🔒 Basic size protection (≈5 MB base64)
    if len(image_base64) > 7_000_000:
        return jsonify({"error": "Image too large"}), 413

    conn = None
    cur = None
    try:
        # 🔥 Upload to Cloudinary (no local file)
        result = cloudinary.uploader.upload(
            base64.b64decode(image_base64),
            folder="skillsphere/profile_images",
            public_id=str(current_user["uid"]),  # overwrite same user image
            overwrite=True,
            resource_type="image"
        )

        image_url = result["secure_url"]

        # 🔥 Save Cloudinary URL in DB
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "UPDATE students SET profile_image=%s WHERE uid=%s",
            (image_url, current_user["uid"])
        )

        conn.commit()

        return jsonify({
            "success": True,
            "profile_image": image_url
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        print("IMAGE UPLOAD ERROR:", repr(e))
        return jsonify({"error": "Image upload failed"}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



from flask import send_from_directory

@app.route("/uploads/profile_images/<path:filename>")
def serve_profile_image(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )




# ============================================================
# LOGOUT
# ============================================================
@app.route("/logout", methods=["POST"])
def logout():
    return jsonify({"success": True}), 200




FORGOT_OTP_TTL = 5 * 60
forgot_otp_store = {}

def load_html_template(filename, **kwargs):
    template_path = os.path.join(os.getcwd(), filename)

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"{filename} not found")

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    for key, value in kwargs.items():
        html = html.replace(f"{{{{{key}}}}}", str(value))

    return html



@app.route("/forgot_password", methods=["POST"])
def forgot_password():
    conn = None
    cur = None
    try:
        data = request.get_json() or {}

        uid = str(data.get("uid", "")).strip()
        if not uid:
            return jsonify({"error": "UID required"}), 400

        # 🔒 Fetch email safely
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT email FROM students WHERE uid=%s",
            (uid,)
        )
        row = cur.fetchone()

        if not row:
            return jsonify({"error": "UID not found"}), 404

        email = row["email"]

    except Exception as e:
        print("FORGOT PASSWORD DB ERROR:", repr(e))
        return jsonify({"error": "Internal server error"}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    # -------------------------------------------------
    # OTP generation (AFTER DB is closed)
    # -------------------------------------------------
    otp = str(random.randint(100000, 999999))
    expires = datetime.utcnow() + timedelta(seconds=FORGOT_OTP_TTL)

    forgot_otp_store[uid] = {
        "otp": otp,
        "expires": expires,
        "verified": False
    }

    html = load_html_template(
        "forgototp.html",
        otp=otp,
        year=datetime.now().year
    )

    # -------------------------------------------------
    # Send email
    # -------------------------------------------------
    try:
        send_email_smtp(
            email,
            "Password Reset OTP — Placement Portal",
            html
        )
    except Exception as e:
        # ❌ Remove OTP if email fails
        forgot_otp_store.pop(uid, None)

        print("FORGOT OTP EMAIL ERROR:", repr(e))
        return jsonify({
            "error": "Failed to send OTP email. Please try again later."
        }), 500

    return jsonify({
        "message": "OTP sent to registered email"
    }), 200




def load_template(otp, template_name):
    template_path = os.path.join(os.getcwd(), template_name)

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"{template_name} not found")

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{otp}}", otp)
    html = html.replace("{{year}}", str(datetime.now().year))
    return html


import requests
import os

def send_email_smtp(to_email, subject, html_body):
    api_key = os.getenv("BREVO_API_KEY")
    if not api_key:
        raise Exception("BREVO_API_KEY not set")

    url = "https://api.brevo.com/v3/smtp/email"

    payload = {
        "sender": {
            "name": "SkillSphere",
            "email": FROM_EMAIL
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_body
    }

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=15)

    if response.status_code not in (200, 201, 202):
        raise Exception(f"Brevo API error: {response.text}")

    print("✅ Email sent via Brevo API to:", to_email)




@app.route("/verify_forgot_otp", methods=["POST"])
def verify_forgot_otp():
    data = request.get_json() or {}

    uid = str(data.get("uid", "")).strip()
    otp = str(data.get("otp", "")).strip()

    if not uid or not otp:
        return jsonify({"error": "UID and OTP required"}), 400

    entry = forgot_otp_store.get(uid)

    if not entry:
        return jsonify({"error": "OTP not requested or expired"}), 400

    if entry.get("verified"):
        return jsonify({"error": "OTP already used"}), 400

    if datetime.utcnow() > entry["expires"]:
        del forgot_otp_store[uid]
        return jsonify({"error": "OTP expired"}), 400

    if otp != entry["otp"]:
        return jsonify({"error": "Invalid OTP"}), 400

    # ✅ Mark OTP as used
    entry["verified"] = True

    return jsonify({"message": "OTP verified"}), 200


@app.route("/reset_password", methods=["POST"])
def reset_password():
    conn = None
    cur = None
    try:
        data = request.get_json() or {}

        uid = str(data.get("uid", "")).strip()
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if not uid or not new_password or not confirm_password:
            return jsonify({"error": "All fields required"}), 400

        if new_password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        entry = forgot_otp_store.get(uid)

        if not entry or not entry.get("verified"):
            return jsonify({"error": "OTP not verified"}), 400

        hashed = generate_password_hash(new_password)

        conn = get_db()
        conn.begin()
        cur = conn.cursor()

        cur.execute(
            "UPDATE students SET password=%s WHERE uid=%s",
            (hashed, uid)
        )

        if cur.rowcount == 0:
            conn.rollback()
            return jsonify({"error": "User not found"}), 404

        conn.commit()

        # ✅ OTP cleanup ONLY after successful commit
        forgot_otp_store.pop(uid, None)

        return jsonify({
            "message": "Password reset successful"
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        print("RESET PASSWORD ERROR:", repr(e))
        return jsonify({"error": "Password reset failed"}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


#/////////////////////////////////////////////////////////////////////////////////////////////////////////////
#NO CHANGE ABOVE THIUS LINE
#/////////////////////////////////////////////////////////////////////////////////////////////////////////////


def build_daily_mcq_prompt(topics, difficulty):
    difficulty_map = {
        "easy": "easy, basic, beginner-friendly",
        "medium": "moderate, conceptual, exam-oriented",
        "hard": "difficult, tricky, placement-level",
        "very hard": "extremely difficult, trap-based, company-style"
    }

    difficulty_text = difficulty_map.get(
        difficulty.lower(),
        "difficult, placement-level"
    )

    return f"""
Act as an elite AI placement MCQ generator for AI engineering students.

Generate exactly 10 {difficulty_text} multiple choice questions.

Topics strictly limited to:
{topics}

Rules:
- One correct option only
- No explanations
- Questions must strictly match the difficulty level
- Avoid repetition
- Output STRICT JSON ONLY

Format:
[
  {{
    "question": "string",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "answer": "A"
  }}
]
"""

def generate_mcqs_from_ai(topics, difficulty):
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = build_daily_mcq_prompt(topics, difficulty)

        response = model.generate_content(prompt)

        text = re.sub(r"```json|```", "", response.text.strip())
        questions = json.loads(text)

        if not isinstance(questions, list) or len(questions) != 10:
            raise Exception("Invalid MCQ format")

        return questions

    except Exception as e:
        print("AI ERROR:", e)
        return []

    

def cleanup_old_quiz(year, uid):
    conn = None
    cur = None
    try:
        today = today_ist()

        cache_table = f"daily_quiz_questions_y{year}"
        bank_table = f"daily_quiz_questions_bank_y{year}"

        conn = get_db()
        conn.begin()   # 🔒 atomic cleanup
        cur = conn.cursor()

        # 🔥 Delete previous-day cached questions
        cur.execute(
            f"""
            DELETE FROM {cache_table}
            WHERE uid=%s AND quiz_date < %s
            """,
            (uid, today)
        )

        # 🔥 Delete previous-day bank questions
        cur.execute(
            f"""
            DELETE FROM {bank_table}
            WHERE uid=%s AND quiz_date < %s
            """,
            (uid, today)
        )

        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        print("CLEANUP OLD QUIZ ERROR:", repr(e))
        # optional: re-raise or just log
        # raise

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_daily_quiz(year, quiz_type, uid):
    conn = None
    cur = None
    try:
        today = today_ist()

        topic_table = f"daily_quiz_topics_y{year}"
        cache_table = f"daily_quiz_questions_y{year}"
        bank_table = f"daily_quiz_questions_bank_y{year}"
        attempts_table = f"daily_quiz_attempts_y{year}"

        conn = get_db()
        conn.begin()   # 🔒 single atomic transaction
        cur = conn.cursor(pymysql.cursors.DictCursor)

        # -------------------------------------------------
        # 🔒 HARD LOCK: allow only ONE quiz per day
        # -------------------------------------------------
        cur.execute(
            f"""
            SELECT id, status
            FROM {attempts_table}
            WHERE uid=%s AND quiz_date=%s
            FOR UPDATE
            """,
            (uid, today)
        )
        existing = cur.fetchone()

        if existing:
            conn.rollback()
            return {"attempted": True}

        # -------------------------------------------------
        # FETCH QUIZ TOPIC
        # -------------------------------------------------
        cur.execute(
            f"""
            SELECT topic, difficulty
            FROM {topic_table}
            WHERE quiz_date=%s AND quiz_type=%s
            """,
            (today, quiz_type)
        )
        topic_row = cur.fetchone()

        if not topic_row:
            conn.rollback()
            return []

        # -------------------------------------------------
        # CREATE ATTEMPT (LOCKED)
        # -------------------------------------------------
        cur.execute(
            f"""
            INSERT INTO {attempts_table}
            (uid, quiz_date, status, score, total, time_taken_seconds)
            VALUES (%s, %s, 'started', 0, 0, 0)
            """,
            (uid, today)
        )

        # -------------------------------------------------
        # COMMIT NOW → quiz officially started
        # -------------------------------------------------
        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        print("GET DAILY QUIZ INIT ERROR:", repr(e))
        return []

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    # -------------------------------------------------
    # GENERATE QUESTIONS (NO DB OPEN)
    # -------------------------------------------------
    questions = generate_mcqs_from_ai(
        topic_row["topic"],
        topic_row["difficulty"]
    )

    if not questions:
        return []

    # -------------------------------------------------
    # STORE QUESTIONS
    # -------------------------------------------------
    conn = None
    cur = None
    try:
        conn = get_db()
        conn.begin()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        frontend_questions = []

        for q in questions:
            correct_answer_text = q["options"][ord(q["answer"]) - ord("A")]

            cur.execute(
                f"""
                INSERT INTO {bank_table}
                (quiz_date, uid, question_text, correct_answer)
                VALUES (%s, %s, %s, %s)
                """,
                (today, uid, q["question"], correct_answer_text)
            )

            qid = cur.lastrowid
            frontend_questions.append({
                "question_id": qid,
                "question": q["question"],
                "options": q["options"]
            })

        cur.execute(
            f"""
            INSERT INTO {cache_table}
            (uid, quiz_date, quiz_type, questions_json)
            VALUES (%s, %s, %s, %s)
            """,
            (uid, today, quiz_type, json.dumps(frontend_questions))
        )

        conn.commit()
        return frontend_questions

    except Exception as e:
        if conn:
            conn.rollback()
        print("GET DAILY QUIZ STORE ERROR:", repr(e))
        return []

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()






def has_attempted_today(year, uid):
    today = today_ist()
    attempts_table = f"daily_quiz_attempts_y{year}"

    db = get_db()
    cur = db.cursor()
    cur.execute(
        f"""
        SELECT 1
        FROM {attempts_table}
        WHERE uid=%s AND quiz_date=%s
        LIMIT 1
        """,
        (uid, today)
    )

    attempted = cur.fetchone() is not None
    cur.close()
    db.close()

    return attempted




def has_attempted_today(year, uid):
    conn = None
    cur = None
    try:
        today = today_ist()
        attempts_table = f"daily_quiz_attempts_y{year}"

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            SELECT 1
            FROM {attempts_table}
            WHERE uid=%s AND quiz_date=%s
            LIMIT 1
            """,
            (uid, today)
        )

        return cur.fetchone() is not None

    except Exception as e:
        print("HAS ATTEMPTED ERROR:", repr(e))
        # Safe default: assume attempted to prevent duplicate quiz
        return True

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



@app.route("/daily_quiz", methods=["GET", "OPTIONS"])
@token_required
def daily_quiz(current_user):

    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    year = int(current_user["year"])
    uid = current_user["uid"]
    quiz_type = "placement"

    # 🔒 BLOCK IF ALREADY ATTEMPTED
    if has_attempted_today(year, uid):
        return jsonify({
            "success": True,
            "attempted": True,
            "message": "Quiz already attempted today"
        }), 200

    questions = get_daily_quiz(year, quiz_type, uid)

    if not questions:
        return jsonify({
            "success": False,
            "attempted": False,
            "message": "No quiz today"
        }), 404

    return jsonify({
        "success": True,
        "attempted": False,
        "quiz_date": today_ist().strftime("%Y-%m-%d"),
        "quiz_type": quiz_type,
        "questions": questions
    }), 200



def resolve_tables(year):
    year = str(year)

    if year == "2":
        return (
            "daily_quiz_attempts_y2",
            "daily_quiz_answers_y2",
            "daily_quiz_questions_bank_y2"
        )
    elif year == "3":
        return (
            "daily_quiz_attempts_y3",
            "daily_quiz_answers_y3",
            "daily_quiz_questions_bank_y3"
        )
    else:
        raise ValueError("Invalid year")



@app.route("/api/profile/today", methods=["GET"])
@token_required
def profile_today(current_user):
    conn = None
    cur = None
    try:
        uid = current_user["uid"]
        year = int(current_user["year"])

        attempts_table, _, _ = resolve_tables(year)

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            SELECT score, total, attempted_at
            FROM {attempts_table}
            WHERE uid=%s AND quiz_date=%s
            """,
            (uid, today_ist())
        )

        row = cur.fetchone()

        if not row:
            return jsonify({
                "attempted": False,
                "message": "Quiz not attempted today"
            }), 200

        return jsonify({
            "attempted": True,
            "score": row["score"],
            "total": row["total"],
            "attempted_at": row["attempted_at"]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route("/api/profile/review", methods=["GET"])
@token_required
def profile_review(current_user):
    conn = None
    cur = None
    try:
        uid = current_user["uid"]              # 🔒 from token
        year = request.args.get("year", type=int)
        quiz_date = request.args.get("quiz_date")  # yyyy-mm-dd

        if not year or not quiz_date:
            return jsonify({"error": "year and quiz_date required"}), 400

        attempts_table, answers_table, questions_table = resolve_tables(year)

        conn = get_db()
        cur = conn.cursor()

        # Step 1: Get attempt ID
        cur.execute(
            f"""
            SELECT id
            FROM {attempts_table}
            WHERE uid=%s AND quiz_date=%s
            """,
            (uid, quiz_date)
        )

        attempt = cur.fetchone()
        if not attempt:
            return jsonify({"error": "Quiz not attempted"}), 404

        attempt_id = attempt["id"]

        # Step 2: Fetch questions + answers
        cur.execute(
            f"""
            SELECT 
                q.question_text,
                q.correct_answer,
                a.selected_answer,
                a.is_correct
            FROM {answers_table} a
            JOIN {questions_table} q
                ON a.question_id = q.id
            WHERE a.attempt_id=%s
            """,
            (attempt_id,)
        )

        rows = cur.fetchall()

        return jsonify({
            "success": True,
            "review": rows
        }), 200

    except Exception as e:
        print("PROFILE REVIEW ERROR:", repr(e))
        return jsonify({"error": "Internal server error"}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



@app.route("/api/profile/status", methods=["GET"])
@token_required
def attempt_status(current_user):
    conn = None
    cur = None
    try:
        uid = current_user["uid"]          # 🔒 from token
        year = request.args.get("year", type=int)

        if not year:
            return jsonify({"error": "year required"}), 400

        attempts_table, _, _ = resolve_tables(year)

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            SELECT 1
            FROM {attempts_table}
            WHERE uid=%s AND quiz_date=%s
            """,
            (uid, today_ist())
        )

        exists = cur.fetchone()

        return jsonify({
            "attempted": bool(exists)
        }), 200

    except Exception as e:
        print("PROFILE STATUS ERROR:", repr(e))
        # Safe default: assume attempted to prevent duplicate quiz
        return jsonify({"attempted": True}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/quiz/submit", methods=["POST", "OPTIONS"])
@token_required
def submit_quiz(current_user):

    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    data = request.json or {}

    uid = current_user["uid"]
    year = int(current_user["year"])
    answers = data.get("answers", [])
    time_taken = data.get("time_taken_seconds")

    if not answers:
        return jsonify({"error": "No answers submitted"}), 400

    attempts_table = f"daily_quiz_attempts_y{year}"
    bank_table = f"daily_quiz_questions_bank_y{year}"
    today = today_ist()

    conn = None
    cur = None

    try:
        conn = get_db()
        conn.begin()              # 🔴 IMPORTANT (disable autocommit for this txn)
        cur = conn.cursor()

        # -------------------------------------------------
        # 🔒 CHECK QUIZ STATUS (LOCK ROW)
        # -------------------------------------------------
        cur.execute(
            f"""
            SELECT status
            FROM {attempts_table}
            WHERE uid=%s AND quiz_date=%s
            FOR UPDATE
            """,
            (uid, today)
        )
        attempt = cur.fetchone()

        if not attempt or attempt["status"] != "started":
            conn.rollback()
            return jsonify({"error": "Quiz already closed"}), 409

        # -------------------------------------------------
        # FETCH CORRECT ANSWERS
        # -------------------------------------------------
        cur.execute(
            f"""
            SELECT id, correct_answer
            FROM {bank_table}
            WHERE uid=%s AND quiz_date=%s
            """,
            (uid, today)
        )

        rows = cur.fetchall()
        if not rows:
            conn.rollback()
            return jsonify({"error": "Quiz not found"}), 400

        correct_map = {r["id"]: r["correct_answer"] for r in rows}
        total_questions = len(correct_map)

        score = 0

        for a in answers:
            qid = a.get("question_id")
            selected = a.get("selected_answer")

            if not qid:
                continue

            qid = int(qid)

            cur.execute(
                f"""
                UPDATE {bank_table}
                SET student_answer=%s
                WHERE id=%s AND uid=%s AND quiz_date=%s
                """,
                (selected, qid, uid, today)
            )

            if selected and selected == correct_map.get(qid):
                score += 1

        # -------------------------------------------------
        # 🔐 FINAL SUBMIT
        # -------------------------------------------------
        cur.execute(
            f"""
            UPDATE {attempts_table}
            SET score=%s,
                total=%s,
                time_taken_seconds=%s,
                status='submitted'
            WHERE uid=%s AND quiz_date=%s
            """,
            (score, total_questions, time_taken, uid, today)
        )

        conn.commit()

        return jsonify({
            "success": True,
            "score": score,
            "total": total_questions
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        print("SUBMIT QUIZ ERROR:", repr(e))
        return jsonify({"error": "Submission failed"}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



@app.route("/api/quiz/review", methods=["GET"])
@token_required
def quiz_review(current_user):
    conn = None
    cur = None
    try:
        uid = current_user["uid"]
        year = int(current_user["year"])

        bank_table = f"daily_quiz_questions_bank_y{year}"
        attempts_table = f"daily_quiz_attempts_y{year}"

        conn = get_db()
        cur = conn.cursor()

        # 1️⃣ Get latest attempt
        cur.execute(
            f"""
            SELECT quiz_date, score, total
            FROM {attempts_table}
            WHERE uid=%s
            ORDER BY quiz_date DESC
            LIMIT 1
            """,
            (uid,)
        )
        attempt = cur.fetchone()

        if not attempt:
            return jsonify({
                "success": True,
                "score": 0,
                "total": 0,
                "answers": []
            }), 200

        quiz_date = attempt["quiz_date"]

        # 2️⃣ Fetch Q + correct + student answers
        cur.execute(
            f"""
            SELECT
                question_text AS question,
                correct_answer,
                student_answer
            FROM {bank_table}
            WHERE uid=%s AND quiz_date=%s
            ORDER BY id ASC
            """,
            (uid, quiz_date)
        )

        rows = cur.fetchall()

        answers = [
            {
                "question": r["question"],
                "your_answer": r["student_answer"],
                "correct_answer": r["correct_answer"],
                "is_correct": r["student_answer"] == r["correct_answer"]
            }
            for r in rows
        ]

        return jsonify({
            "success": True,
            "score": attempt["score"],
            "total": attempt["total"],
            "answers": answers
        }), 200

    except Exception as e:
        print("QUIZ REVIEW ERROR:", repr(e))
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


##################################################################################################################
@app.route("/api/profile/marks_history", methods=["GET"])
@token_required
def marks_history(current_user):
    conn = None
    cur = None
    try:
        uid = current_user["uid"]
        student_year = int(current_user["year"])

        # Validate query params
        month = request.args.get("month", type=int)
        year_filter = request.args.get("year", type=int)

        if not month or not year_filter:
            return jsonify({
                "success": False,
                "error": "month and year are required"
            }), 400

        attempts_table = (
            "daily_quiz_attempts_y2"
            if student_year == 2
            else "daily_quiz_attempts_y3"
        )

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            SELECT quiz_date, score, total
            FROM {attempts_table}
            WHERE uid=%s
              AND MONTH(quiz_date)=%s
              AND YEAR(quiz_date)=%s
            ORDER BY quiz_date DESC
            """,
            (uid, month, year_filter)
        )

        rows = cur.fetchall()

        history = []
        total_scored = 0
        total_possible = 0

        for r in rows:
            total_scored += r["score"]
            total_possible += r["total"]
            history.append({
                "quiz_date": r["quiz_date"].strftime("%Y-%m-%d"),
                "score": r["score"],
                "total": r["total"]
            })

        return jsonify({
            "success": True,
            "history": history,
            "total_scored": total_scored,
            "total_possible": total_possible
        }), 200

    except Exception as e:
        print("MARKS HISTORY ERROR:", repr(e))
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


    

@app.route("/api/leaderboard", methods=["GET"])
@token_required
def leaderboard(current_user):
    conn = None
    cur = None
    try:
        year = int(current_user["year"])

        # IST current month & year
        ist = pytz.timezone("Asia/Kolkata")
        now = datetime.now(ist)
        current_month = now.month
        current_year = now.year

        attempts_table = (
            "daily_quiz_attempts_y2"
            if year == 2
            else "daily_quiz_attempts_y3"
        )

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            SELECT 
                s.name,
                SUM(a.score) AS total_score
            FROM {attempts_table} a
            JOIN students s ON s.uid = a.uid
            WHERE MONTH(a.quiz_date)=%s
              AND YEAR(a.quiz_date)=%s
            GROUP BY a.uid, s.name
            ORDER BY total_score DESC
            LIMIT 10
            """,
            (current_month, current_year)
        )

        top10 = cur.fetchall()

        return jsonify({
            "success": True,
            "month": now.strftime("%B"),
            "top10": top10
        }), 200

    except Exception as e:
        print("LEADERBOARD ERROR:", repr(e))
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()






@app.route("/api/quiz/today/status", methods=["GET"])
@token_required
def today_quiz_status(current_user):
    conn = None
    cur = None
    try:
        uid = current_user["uid"]
        year = int(current_user["year"])

        attempts_table, _, _ = resolve_tables(year)
        today = today_ist()

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            SELECT id FROM {attempts_table}
            WHERE uid=%s AND quiz_date=%s
            """,
            (uid, today)
        )

        attempted = cur.fetchone() is not None

        return jsonify({
            "available": True,
            "attempted": attempted
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()




#########################################################################################
# faculty quiz routes
#############################################################################################3

import pymysql

@app.route("/faculty_quiz", methods=["GET", "OPTIONS"])
@token_required
def faculty_quiz(current_user):

    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    conn = None
    cur = None
    try:
        uid = current_user["uid"]
        year = int(current_user["year"])
        quiz_id = request.args.get("quiz_id", type=int)

        if not quiz_id:
            return jsonify({
                "success": False,
                "message": "quiz_id required"
            }), 400

        marks_table = (
            "assignment_quiz_marks_y2"
            if year == 2
            else "assignment_quiz_marks_y3"
        )

        conn = get_db()
        cur = conn.cursor(pymysql.cursors.Cursor)  # tuple cursor

        # 1️⃣ Check quiz exists
        cur.execute(
            """
            SELECT quiz_id
            FROM faculty_quiz_master
            WHERE quiz_id=%s AND year=%s
            """,
            (quiz_id, year),
        )

        if not cur.fetchone():
            return jsonify({
                "success": False,
                "message": "Quiz not found"
            }), 404

        # 2️⃣ Check already attempted
        cur.execute(
            f"""
            SELECT id
            FROM {marks_table}
            WHERE uid=%s AND quiz_id=%s
            """,
            (uid, quiz_id),
        )

        if cur.fetchone():
            return jsonify({
                "success": True,
                "attempted": True
            }), 200

        # 3️⃣ Fetch questions
        cur.execute(
            """
            SELECT id, question, option_a, option_b, option_c, option_d
            FROM faculty_quiz_questions_new
            WHERE quiz_id=%s
            """,
            (quiz_id,),
        )

        rows = cur.fetchall()
        if not rows:
            return jsonify({
                "success": False,
                "message": "No questions found"
            }), 404

        questions = [
            {
                "question_id": r[0],
                "question": r[1],
                "option_a": r[2],
                "option_b": r[3],
                "option_c": r[4],
                "option_d": r[5],
            }
            for r in rows
        ]

        return jsonify({
            "success": True,
            "attempted": False,
            "quiz_id": quiz_id,
            "questions": questions
        }), 200

    except Exception as e:
        print("FACULTY QUIZ ERROR:", repr(e))
        return jsonify({"error": "Internal server error"}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/faculty_quiz/submit", methods=["POST"])
@token_required
def assignment_submit(current_user):

    conn = None
    cur = None
    try:
        uid = current_user["uid"]
        year = int(current_user["year"])

        data = request.json or {}
        answers = data.get("answers", [])
        quiz_id = data.get("quiz_id")

        if quiz_id is None:
            return jsonify({"error": "Quiz ID missing"}), 400

        today = today_ist()

        marks_table = (
            "assignment_quiz_marks_y2"
            if year == 2
            else "assignment_quiz_marks_y3"
        )

        conn = get_db()
        conn.begin()   # 🔒 force transaction
        cur = conn.cursor(pymysql.cursors.DictCursor)

        # 🔒 Prevent reattempt (LOCK)
        cur.execute(
            f"""
            SELECT id
            FROM {marks_table}
            WHERE uid=%s AND quiz_id=%s
            FOR UPDATE
            """,
            (uid, quiz_id),
        )

        if cur.fetchone():
            conn.rollback()
            return jsonify({"error": "Quiz already submitted"}), 409

        # 🔹 Fetch ALL correct answers for quiz
        cur.execute(
            """
            SELECT id, correct_option
            FROM faculty_quiz_questions_new
            WHERE quiz_id=%s
            """,
            (quiz_id,),
        )

        rows = cur.fetchall()
        total_questions = len(rows)

        correct_map = {r["id"]: r["correct_option"] for r in rows}

        score = 0

        for a in answers:
            qid = a.get("question_id")
            selected = a.get("selected_answer")

            if qid is None or selected is None:
                continue

            if correct_map.get(qid) == selected:
                score += 1

        # 🧾 Store attempt
        cur.execute(
            f"""
            INSERT INTO {marks_table}
            (uid, quiz_id, quiz_date, total_questions, score, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (uid, quiz_id, today, total_questions, score, "Admin"),
        )

        conn.commit()

        return jsonify({
            "success": True,
            "score": score,
            "total": total_questions
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        print("FACULTY SUBMIT ERROR:", repr(e))
        return jsonify({"error": "Submission failed"}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



@app.route("/api/profile/faculty_quiz/today", methods=["GET"])
@token_required
def faculty_quiz_today_marks(current_user):
    conn = None
    cur = None
    try:
        uid = current_user["uid"]
        year = int(current_user["year"])
        today = today_ist()

        quiz_table = "faculty_quiz_master"
        marks_table = (
            "assignment_quiz_marks_y2"
            if year == 2
            else "assignment_quiz_marks_y3"
        )

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT quiz_id, quiz_date, quiz_start_time, quiz_end_time
            FROM faculty_quiz_master
            WHERE quiz_date=%s AND year=%s
            """,
            (today, year),
        )

        quizzes = cur.fetchall()

        if not quizzes:
            return jsonify({"exists": False}), 200

        quiz_ids = [q["quiz_id"] for q in quizzes]
        placeholders = ",".join(["%s"] * len(quiz_ids))

        cur.execute(
            f"""
            SELECT quiz_id, score
            FROM {marks_table}
            WHERE uid=%s AND quiz_id IN ({placeholders})
              AND quiz_date=%s
            """,
            (uid, *quiz_ids, today),
        )

        marks_map = {m["quiz_id"]: m["score"] for m in cur.fetchall()}

        result = [
            {
                "quiz_id": q["quiz_id"],
                "quiz_date": q["quiz_date"].strftime("%Y-%m-%d"),
                "quiz_start_time": str(q["quiz_start_time"]),
                "quiz_end_time": str(q["quiz_end_time"]),
                "attempted": q["quiz_id"] in marks_map,
                "score": marks_map.get(q["quiz_id"])
            }
            for q in quizzes
        ]

        return jsonify({
            "exists": True,
            "quizzes": result
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



@app.route("/api/profile/faculty_quiz/history", methods=["GET"])
@token_required
def faculty_quiz_marks_history(current_user):
    conn = None
    cur = None
    try:
        uid = current_user["uid"]
        year = int(current_user["year"])

        marks_table = (
            "assignment_quiz_marks_y2"
            if year == 2
            else "assignment_quiz_marks_y3"
        )

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            SELECT
                m.quiz_id,
                m.quiz_date,
                m.score,
                m.total_questions,
                q.created_by AS quiz_created_by
            FROM {marks_table} m
            JOIN faculty_quiz_master q
                ON m.quiz_id = q.quiz_id
            WHERE m.uid = %s
            ORDER BY m.quiz_date DESC
            """,
            (uid,),
        )

        rows = cur.fetchall()

        history = [
            {
                "quiz_id": r["quiz_id"],
                "quiz_date": r["quiz_date"].strftime("%Y-%m-%d"),
                "score": r["score"],
                "total_questions": r["total_questions"],
                "created_by": r["quiz_created_by"]
            }
            for r in rows
        ]

        return jsonify({
            "success": True,
            "history": history
        }), 200

    except Exception as e:
        print("FACULTY QUIZ HISTORY ERROR:", repr(e))
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



@app.route("/faculty_quiz/list", methods=["GET"])
@token_required
def faculty_quiz_list(current_user):
    conn = None
    cur = None
    try:
        uid = current_user["uid"]
        year = int(current_user["year"])
        today = today_ist()

        marks_table = (
            "assignment_quiz_marks_y2"
            if year == 2
            else "assignment_quiz_marks_y3"
        )

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT quiz_id, quiz_date, quiz_start_time,
                   quiz_end_time, created_by
            FROM faculty_quiz_master
            WHERE quiz_date=%s AND year=%s
            ORDER BY quiz_start_time
            """,
            (today, year),
        )

        quizzes = cur.fetchall()

        if not quizzes:
            return jsonify({
                "success": True,
                "count": 0,
                "quizzes": []
            }), 200

        quiz_ids = [q["quiz_id"] for q in quizzes]
        placeholders = ",".join(["%s"] * len(quiz_ids))

        cur.execute(
            f"""
            SELECT DISTINCT quiz_id
            FROM {marks_table}
            WHERE uid=%s AND quiz_id IN ({placeholders})
            """,
            (uid, *quiz_ids),
        )

        attempted_ids = {r["quiz_id"] for r in cur.fetchall()}

        result = [
            {
                "quiz_id": q["quiz_id"],
                "quiz_date": q["quiz_date"].strftime("%Y-%m-%d"),
                "quiz_start_time": str(q["quiz_start_time"]),
                "quiz_end_time": str(q["quiz_end_time"]),
                "created_by": q["created_by"],
                "attempted": False
            }
            for q in quizzes
            if q["quiz_id"] not in attempted_ids
        ]

        return jsonify({
            "success": True,
            "count": len(result),
            "quizzes": result
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()





# ============================================================
# RUN SERVER
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port
    )


