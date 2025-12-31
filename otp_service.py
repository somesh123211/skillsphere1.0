from dotenv import load_dotenv
load_dotenv()

import os
import random
import datetime
import smtplib
from email.mime.text import MIMEText


# ---------------- CONFIG ----------------
SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 587
SMTP_USER = "9da39b001@smtp-brevo.com"
SMTP_PASS = os.environ.get("BREVO_SMTP_PASS")

FROM_EMAIL = "techpallotine@gmail.com"
OTP_TTL_SECONDS = 5 * 60
MAX_ATTEMPTS = 3
# ---------------------------------------

otp_store = {}  # email -> {otp, expires_at, attempts}


def generate_otp():
    return f"{random.randint(100000, 999999):06d}"


def load_template(otp):
    template_path = os.path.join(
        os.path.dirname(__file__),
        "otp_template.html"
    )

    if not os.path.exists(template_path):
        raise FileNotFoundError("otp_template.html not found")

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{otp}}", otp)
    html = html.replace("{{year}}", str(datetime.datetime.now().year))
    return html


def send_email_smtp(to_email, subject, html_body):
    if not SMTP_PASS:
        raise EnvironmentError("BREVO_SMTP_PASS not set")

    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


def send_otp_email(email):
    otp = generate_otp()
    html_body = load_template(otp)

    send_email_smtp(
        email,
        "Your Verification Code — Placement Portal",
        html_body
    )

    expires_at = datetime.datetime.utcnow() + datetime.timedelta(
        seconds=OTP_TTL_SECONDS
    )

    otp_store[email.lower()] = {
        "otp": otp,
        "expires_at": expires_at,
        "attempts": 0
    }

    # REMOVE THIS IN PRODUCTION
    print("OTP sent (testing only):", otp)


def verify_otp(email, entered):
    key = email.lower()

    if key not in otp_store:
        return False, "No OTP found. Request a new one."

    entry = otp_store[key]

    if datetime.datetime.utcnow() > entry["expires_at"]:
        del otp_store[key]
        return False, "OTP expired"

    if entry["attempts"] >= MAX_ATTEMPTS:
        del otp_store[key]
        return False, "Maximum attempts exceeded"

    entry["attempts"] += 1

    if entered == entry["otp"]:
        del otp_store[key]
        return True, "OTP verified"

    remaining = MAX_ATTEMPTS - entry["attempts"]
    return False, f"Invalid OTP. {remaining} attempt(s) left"
