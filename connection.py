# ─────────────────────────────────────────────────────────────────────────────
#  connection.py  –  Reads all credentials from .env file (or Render env vars)
#  Keep .env OUT of version control (add to .gitignore)
# ─────────────────────────────────────────────────────────────────────────────

from dotenv import load_dotenv
import os

load_dotenv()  # loads all values from .env into environment

# ── Flask ─────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv('SECRET_KEY')

# ── PostgreSQL ────────────────────────────────────────────────────────────────
# FIX: psycopg2 requires 'dbname' not 'database'
# Supports both DATABASE_URL (Render managed DB) and individual vars
_DATABASE_URL = os.getenv('DATABASE_URL')

if _DATABASE_URL:
    # Render provides a full postgres:// URL — psycopg2 accepts it directly
    # but 'postgres://' scheme must be replaced with 'postgresql://'
    DB_CONFIG = {'dsn': _DATABASE_URL.replace('postgres://', 'postgresql://', 1)}
else:
    DB_CONFIG = {
        'host':     os.getenv('DB_HOST'),
        'user':     os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'dbname':   os.getenv('DB_NAME'),   # FIX: was 'database', psycopg2 needs 'dbname'
        'port':     os.getenv('DB_PORT', '5432'),
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
# FIX: Default to Linux path for Render; override via env var for local Windows dev
WKHTMLTOPDF_PATH = os.getenv('WKHTMLTOPDF_PATH', '/usr/bin/wkhtmltopdf')

PDF_OPTIONS = {
    'page-size':      'A4',
    'margin-top':     '0.75in',
    'margin-right':   '0.75in',
    'margin-bottom':  '0.75in',
    'margin-left':    '0.75in',
    'encoding':       'UTF-8',
    'no-outline':     None
}
