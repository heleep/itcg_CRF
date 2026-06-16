# ─────────────────────────────────────────────────────────────────────────────
#  connection.py  –  Reads all credentials from .env file
#  Keep .env OUT of version control (add to .gitignore)
# ─────────────────────────────────────────────────────────────────────────────

from dotenv import load_dotenv
import os

load_dotenv()  # loads all values from .env into environment

# ── Flask ─────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv('SECRET_KEY')

# ── MySQL ─────────────────────────────────────────────────────────────────────
DB_CONFIG = {
    'host':     os.getenv('DB_HOST'),
    'user':     os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# ── Email (SMTP / Flask-Mail) ─────────────────────────────────────────────────
MAIL_SERVER         = os.getenv('MAIL_SERVER')
MAIL_PORT           = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS        = os.getenv('MAIL_USE_TLS', 'True') == 'True'
MAIL_USERNAME       = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD       = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

# ── Accountant (static / BCC) email ──────────────────────────────────────────
ACCOUNTANT_EMAIL = os.getenv('ACCOUNTANT_EMAIL')

# ── wkhtmltopdf ───────────────────────────────────────────────────────────────
WKHTMLTOPDF_PATH = os.getenv('WKHTMLTOPDF_PATH')

PDF_OPTIONS = {
    'page-size':      'A4',
    'margin-top':     '0.75in',
    'margin-right':   '0.75in',
    'margin-bottom':  '0.75in',
    'margin-left':    '0.75in',
    'encoding':       'UTF-8',
    'no-outline':     None
}
