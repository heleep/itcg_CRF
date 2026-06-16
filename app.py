from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import pdfkit
import os
import tempfile
import random
import string
import base64
from flask_mail import Mail, Message

# ── Import all credentials from connection.py ─────────────────────────────────
from connection import (
    SECRET_KEY,
    DB_CONFIG,
    MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS,
    MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER,
    ACCOUNTANT_EMAIL,
    WKHTMLTOPDF_PATH,
    PDF_OPTIONS
)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ── Mail config (values come from connection.py) ──────────────────────────────
app.config['MAIL_SERVER']         = MAIL_SERVER
app.config['MAIL_PORT']           = MAIL_PORT
app.config['MAIL_USE_TLS']        = MAIL_USE_TLS
app.config['MAIL_USERNAME']       = MAIL_USERNAME
app.config['MAIL_PASSWORD']       = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER

mail = Mail(app)

# ── pdfkit (path comes from connection.py) ────────────────────────────────────
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

# ── ITCG Logo (base64, embedded into generated PDFs) ──────────────────────────
_ITCG_LOGO_B64 = None


def get_itcg_logo_b64():
    """Read and cache the ITCG logo as a base64 data URI for use in PDFs."""
    global _ITCG_LOGO_B64
    if _ITCG_LOGO_B64 is None:
        try:
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'itcg-logo-teal.png')
            with open(logo_path, 'rb') as f:
                _ITCG_LOGO_B64 = 'data:image/png;base64,' + base64.b64encode(f.read()).decode('utf-8')
        except Exception:
            _ITCG_LOGO_B64 = ''
    return _ITCG_LOGO_B64


def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None


def create_tables():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_verification (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                otp VARCHAR(6) NOT NULL,
                purpose VARCHAR(50) DEFAULT 'form_submit',
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email ON otp_verification (email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expires ON otp_verification (expires_at)")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id SERIAL PRIMARY KEY,
                registration_number VARCHAR(50),
                domain_type VARCHAR(50),
                industry_reg_type VARCHAR(50),
                vendor_name VARCHAR(255),
                website VARCHAR(255),
                industry_type VARCHAR(100),
                contact_no VARCHAR(50),
                cin_no VARCHAR(100),
                llpin_no VARCHAR(100),
                tan_no VARCHAR(100),
                gst VARCHAR(100),
                gst_certificate VARCHAR(10),
                pan VARCHAR(100),
                pan_certificate VARCHAR(10),
                msme_no VARCHAR(100),
                billing_address_type VARCHAR(100),
                billing_line1 TEXT,
                billing_line2 TEXT,
                billing_line3 TEXT,
                billing_city VARCHAR(100),
                billing_state VARCHAR(100),
                billing_pin VARCHAR(50),
                shipping_address_type VARCHAR(100),
                shipping_line1 TEXT,
                shipping_line2 TEXT,
                shipping_line3 TEXT,
                shipping_city VARCHAR(100),
                shipping_state VARCHAR(100),
                shipping_pin VARCHAR(50),
                bank_name VARCHAR(255),
                branch_name VARCHAR(255),
                account_no VARCHAR(100),
                account_type VARCHAR(100),
                ifsc VARCHAR(50),
                micr VARCHAR(50),
                it_contact_name VARCHAR(255),
                it_designation VARCHAR(255),
                it_email VARCHAR(255),
                it_mobile VARCHAR(50),
                it_landline VARCHAR(50),
                purchase_contact_name VARCHAR(255),
                purchase_designation VARCHAR(255),
                purchase_email VARCHAR(255),
                purchase_mobile VARCHAR(50),
                purchase_landline VARCHAR(50),
                accounts_contact_name VARCHAR(255),
                accounts_designation VARCHAR(255),
                accounts_email VARCHAR(255),
                accounts_mobile VARCHAR(50),
                accounts_landline VARCHAR(50),
                finance_contact_name VARCHAR(255),
                finance_designation VARCHAR(255),
                finance_email VARCHAR(255),
                finance_mobile VARCHAR(50),
                finance_landline VARCHAR(50),
                declarant_name VARCHAR(255),
                declarant_designation VARCHAR(255),
                declarant_email VARCHAR(255),
                declarant_date DATE,
                declarant_signature VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("Tables created successfully")


# ── OTP Helpers ───────────────────────────────────────────────────────────────

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def generate_pdf_for_registration(registration_id):
    """Generate a PDF bytes object for a given registration_id. Returns (bytes, data) or None."""
    try:
        conn = get_db_connection()
        if not conn:
            return None
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM registrations WHERE id = %s", (registration_id,))
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        if not data:
            return None
        data = dict(data)
        if data.get('declarant_date') and hasattr(data['declarant_date'], 'strftime'):
            data['declarant_date'] = data['declarant_date'].strftime('%d-%m-%Y')
        html_content = render_template('pdf_template.html', data=data, itcg_logo=get_itcg_logo_b64())
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdfkit.from_string(html_content, tmp.name, configuration=PDFKIT_CONFIG, options=PDF_OPTIONS)
            tmp_path = tmp.name
        with open(tmp_path, 'rb') as f:
            pdf_bytes = f.read()
        os.unlink(tmp_path)
        return pdf_bytes, data
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None


def send_otp_email(email, otp, registration_id=None):
    try:
        msg = Message(
            subject="ITCG - Verify Your Submission OTP",
            recipients=[email]
        )
        msg.html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;
                    border:1px solid #ddd;border-radius:10px;">
            <h2 style="color:#1a4b7a;border-bottom:2px solid #1a4b7a;padding-bottom:10px;">
                ITCG Vendor Registration Portal
            </h2>
            <p style="font-size:16px;">Dear Declarant,</p>
            <p style="font-size:16px;">
                Your vendor registration form has been received successfully.<br>
                Please review the <strong>attached PDF</strong> to confirm your submitted details,
                then use the OTP below to verify and complete your submission.
            </p>
            <div style="background:#f0f0f0;padding:15px;text-align:center;
                        font-size:36px;font-weight:bold;letter-spacing:8px;
                        border-radius:5px;margin:20px 0;color:#1a4b7a;">
                {otp}
            </div>
            <p style="font-size:14px;color:#e53e3e;font-weight:bold;">
                Please confirm your details in the attached PDF before entering the OTP.
            </p>
            <p style="font-size:14px;color:#666;">
                This OTP is valid for <strong>10 minutes</strong>.
            </p>
            <p style="font-size:14px;color:#666;">
                If you did not submit this form, please ignore this email.
            </p>
            <hr style="border:1px solid #ddd;margin:20px 0;">
            <p style="font-size:12px;color:#999;">Regards,<br>ITCG Team</p>
        </div>
        """
        if registration_id:
            result = generate_pdf_for_registration(registration_id)
            if result:
                pdf_bytes, reg_data = result
                reg_number = reg_data.get('registration_number', registration_id)
                msg.attach(
                    filename=f"ITCG_Registration_{reg_number}.pdf",
                    content_type="application/pdf",
                    data=pdf_bytes
                )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_confirmation_email(declarant_email, registration_id):
    try:
        result = generate_pdf_for_registration(registration_id)
        if not result:
            return False
        pdf_bytes, reg_data = result
        reg_number  = reg_data.get('registration_number', registration_id)
        vendor_name = reg_data.get('vendor_name', 'Vendor')

        msg = Message(
            subject=f"ITCG - Registration Confirmed: {reg_number}",
            recipients=[declarant_email]
        )

        if declarant_email.lower() != ACCOUNTANT_EMAIL.lower():
            msg.bcc = [ACCOUNTANT_EMAIL]

        msg.html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;
                    border:1px solid #ddd;border-radius:10px;">
            <h2 style="color:#1a4b7a;border-bottom:2px solid #1a4b7a;padding-bottom:10px;">
                ITCG Vendor Registration Portal
            </h2>
            <p style="font-size:16px;">Dear {vendor_name},</p>
            <p style="font-size:16px;">
                Your vendor registration has been <strong style="color:#059669;">confirmed successfully</strong>.
            </p>
            <div style="background:#f0fff4;border:1px solid #9ae6b4;border-radius:8px;
                        padding:14px 18px;margin:20px 0;">
                <p style="font-size:14px;color:#276749;margin:0;">
                    <strong>Registration Number:</strong> {reg_number}
                </p>
            </div>
            <p style="font-size:14px;color:#555;">
                Please find the complete registration document and all uploaded certificates
                attached to this email for your records.
            </p>
            <hr style="border:1px solid #ddd;margin:20px 0;">
            <p style="font-size:12px;color:#999;">Regards,<br>ITCG Team</p>
        </div>
        """

        msg.attach(
            filename=f"ITCG_Registration_{reg_number}_Confirmed.pdf",
            content_type="application/pdf",
            data=pdf_bytes
        )

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        doc_folders = {
            'GST':  reg_data.get('gst', ''),
            'PAN':  reg_data.get('pan', ''),
            'MSME': reg_data.get('msme_no', ''),
        }
        for doc_type, doc_number in doc_folders.items():
            if not doc_number or doc_number.upper() == 'NA':
                continue
            folder = os.path.join(BASE_DIR, 'uploads', doc_type)
            if not os.path.isdir(folder):
                continue
            for ext in ['.pdf', '.jpg', '.jpeg', '.png']:
                file_path = os.path.join(folder, doc_number + ext)
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as df:
                        content_type = 'application/pdf' if ext == '.pdf' else f'image/{ext.lstrip(".")}'
                        msg.attach(
                            filename=f"{doc_type}_Certificate_{doc_number}{ext}",
                            content_type=content_type,
                            data=df.read()
                        )
                    break

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending confirmation email: {e}")
        return False


def save_otp(email, otp, expiry_minutes=10):
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(minutes=expiry_minutes)
    cursor.execute("DELETE FROM otp_verification WHERE email = %s", (email,))
    cursor.execute(
        "INSERT INTO otp_verification (email, otp, purpose, expires_at) VALUES (%s, %s, %s, %s)",
        (email, otp, 'form_submit', expires_at)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True


def verify_otp(email, otp):
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT * FROM otp_verification WHERE email=%s AND otp=%s AND purpose='form_submit' "
        "AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1",
        (email, otp)
    )
    result = cursor.fetchone()
    if result:
        cursor.execute("DELETE FROM otp_verification WHERE id=%s", (result['id'],))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    cursor.close()
    conn.close()
    return False


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/registration')
def registration_page():
    return render_template('index.html')


# ── STEP 1: Form submit → save to DB, send OTP ────────────────────────────────

@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        data = request.json
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = conn.cursor()

        query = """
        INSERT INTO registrations (
            registration_number, domain_type, industry_reg_type, vendor_name, website, industry_type, contact_no,
            cin_no, llpin_no, tan_no, gst, gst_certificate, pan, pan_certificate, msme_no,
            billing_address_type, billing_line1, billing_line2, billing_line3,
            billing_city, billing_state, billing_pin,
            shipping_address_type, shipping_line1, shipping_line2, shipping_line3,
            shipping_city, shipping_state, shipping_pin,
            bank_name, branch_name, account_no, account_type, ifsc, micr,
            it_contact_name, it_designation, it_email, it_mobile, it_landline,
            purchase_contact_name, purchase_designation, purchase_email, purchase_mobile, purchase_landline,
            accounts_contact_name, accounts_designation, accounts_email, accounts_mobile, accounts_landline,
            finance_contact_name, finance_designation, finance_email, finance_mobile, finance_landline,
            declarant_name, declarant_designation, declarant_email, declarant_date, declarant_signature
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        ) RETURNING id
        """

        values = (
            data.get('registrationNumber'), data.get('domainType'), data.get('industryRegType'),
            data.get('vendorName'), data.get('website'), data.get('industry'),
            data.get('contactNo'), data.get('cin'), data.get('llpin'), data.get('tan'),
            data.get('gst'), data.get('gstCert'), data.get('pan'), data.get('panCert'), data.get('msme'),
            data.get('billType'), data.get('billLine1'), data.get('billLine2'),
            data.get('billLine3'), data.get('billCity'), data.get('billState'),
            data.get('billPin'), data.get('shipType'), data.get('shipLine1'),
            data.get('shipLine2'), data.get('shipLine3'), data.get('shipCity'),
            data.get('shipState'), data.get('shipPin'),
            data.get('bankName'), data.get('branchName'), data.get('accountNo'),
            data.get('accountType'), data.get('ifsc'), data.get('micr'),
            data.get('itName'), data.get('itDesig'), data.get('itEmail'),
            data.get('itMobile'), data.get('itLandline'),
            data.get('purName'), data.get('purDesig'), data.get('purEmail'),
            data.get('purMobile'), data.get('purLandline'),
            data.get('accName'), data.get('accDesig'), data.get('accEmail'),
            data.get('accMobile'), data.get('accLandline'),
            data.get('finName'), data.get('finDesig'), data.get('finEmail'),
            data.get('finMobile'), data.get('finLandline'),
            data.get('declName'), data.get('declDesig'), data.get('declEmail'),
            data.get('declDate'), data.get('signature')
        )

        cursor.execute(query, values)
        registration_id = cursor.fetchone()[0]  # PostgreSQL RETURNING id
        conn.commit()
        cursor.close()
        conn.close()

        decl_email = data.get('declEmail', '').strip()
        if not decl_email:
            return jsonify({'success': False, 'error': 'Declarant email is required'}), 400

        otp = generate_otp()
        if save_otp(decl_email, otp):
            if send_otp_email(decl_email, otp, registration_id=registration_id):
                session['pending_registration_id'] = registration_id
                session['pending_email'] = decl_email
                return jsonify({
                    'success': True,
                    'message': 'OTP sent to declarant email',
                    'id': registration_id,
                    'registrationNumber': data.get('registrationNumber'),
                    'requireOtp': True
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Form saved but failed to send OTP. Check your email configuration.'
                }), 500

        return jsonify({'success': False, 'error': 'Failed to generate OTP'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── STEP 2: Verify OTP ────────────────────────────────────────────────────────

@app.route('/api/verify-submission-otp', methods=['POST'])
def verify_submission_otp():
    data = request.json
    otp = data.get('otp', '').strip()

    email = session.get('pending_email')
    registration_id = session.get('pending_registration_id')

    if not email or not registration_id:
        return jsonify({'success': False, 'error': 'Session expired. Please resubmit the form.'}), 400

    if verify_otp(email, otp):
        session['verified_registration_id'] = registration_id
        session.pop('pending_registration_id', None)
        session.pop('pending_email', None)
        return jsonify({'success': True, 'previewUrl': f'/registration-options/{registration_id}'})

    return jsonify({'success': False, 'error': 'Invalid or expired OTP. Please try again.'}), 400


@app.route('/api/resend-otp', methods=['POST'])
def resend_otp():
    email = session.get('pending_email')
    if not email:
        return jsonify({'success': False, 'error': 'Session expired.'}), 400
    otp = generate_otp()
    if save_otp(email, otp) and send_otp_email(email, otp):
        return jsonify({'success': True, 'message': 'OTP resent successfully'})
    return jsonify({'success': False, 'error': 'Failed to resend OTP'}), 500


# ── Upload Documents ──────────────────────────────────────────────────────────

@app.route('/upload-documents', methods=['POST'])
def upload_documents():
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        gst_folder  = os.path.join(BASE_DIR, 'uploads', 'GST')
        pan_folder  = os.path.join(BASE_DIR, 'uploads', 'PAN')
        msme_folder = os.path.join(BASE_DIR, 'uploads', 'MSME')
        os.makedirs(gst_folder,  exist_ok=True)
        os.makedirs(pan_folder,  exist_ok=True)
        os.makedirs(msme_folder, exist_ok=True)

        gst_number  = request.form.get('gst_number',  '').strip()
        pan_number  = request.form.get('pan_number',  '').strip()
        msme_number = request.form.get('msme_number', '').strip()
        saved = []

        gst_file = request.files.get('gstFile')
        if gst_file and gst_file.filename and gst_number:
            ext = os.path.splitext(gst_file.filename)[1].lower() or '.pdf'
            gst_file.save(os.path.join(gst_folder, gst_number + ext))
            saved.append('GST')

        pan_file = request.files.get('panFile')
        if pan_file and pan_file.filename and pan_number:
            ext = os.path.splitext(pan_file.filename)[1].lower() or '.pdf'
            pan_file.save(os.path.join(pan_folder, pan_number + ext))
            saved.append('PAN')

        msme_file = request.files.get('msmeFile')
        if msme_file and msme_file.filename:
            safe_name = msme_number if msme_number else 'msme_doc'
            ext = os.path.splitext(msme_file.filename)[1].lower() or '.pdf'
            msme_file.save(os.path.join(msme_folder, safe_name + ext))
            saved.append('MSME')

        return jsonify({'success': True, 'saved': saved})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── Registration Options ──────────────────────────────────────────────────────

@app.route('/registration-options/<int:registration_id>')
def registration_options(registration_id):
    if session.get('verified_registration_id') != registration_id:
        return redirect(url_for('home'))
    try:
        conn = get_db_connection()
        if not conn:
            return redirect(url_for('home'))
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM registrations WHERE id = %s", (registration_id,))
        data = dict(cursor.fetchone())
        cursor.close()
        conn.close()
        if not data:
            return redirect(url_for('home'))
        return render_template('options.html', data=data)
    except Exception:
        return redirect(url_for('home'))


# ── Preview ───────────────────────────────────────────────────────────────────

@app.route('/preview/<int:registration_id>')
def preview_registration(registration_id):
    if session.get('verified_registration_id') != registration_id:
        return redirect(url_for('home'))
    try:
        conn = get_db_connection()
        if not conn:
            return redirect(url_for('home'))
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM registrations WHERE id = %s", (registration_id,))
        data = dict(cursor.fetchone())
        cursor.close()
        conn.close()
        if not data:
            return redirect(url_for('home'))
        if data.get('declarant_date') and hasattr(data['declarant_date'], 'strftime'):
            data['declarant_date'] = data['declarant_date'].strftime('%d-%m-%Y')
        return render_template('preview.html', data=data)
    except Exception:
        return redirect(url_for('home'))


# ── Edit Form ─────────────────────────────────────────────────────────────────

@app.route('/edit-form/<int:registration_id>')
def edit_form(registration_id):
    if session.get('verified_registration_id') != registration_id:
        return redirect(url_for('home'))
    try:
        conn = get_db_connection()
        if not conn:
            return redirect(url_for('home'))
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM registrations WHERE id = %s", (registration_id,))
        data = dict(cursor.fetchone())
        cursor.close()
        conn.close()
        if not data:
            return redirect(url_for('home'))
        if data.get('declarant_date') and hasattr(data['declarant_date'], 'strftime'):
            data['declarant_date'] = data['declarant_date'].strftime('%Y-%m-%d')
        return render_template('edit_form.html', data=data)
    except Exception:
        return redirect(url_for('home'))


# ── Update ────────────────────────────────────────────────────────────────────

@app.route('/update/<int:registration_id>', methods=['POST'])
def update_registration(registration_id):
    if session.get('verified_registration_id') != registration_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    try:
        data = request.json
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        cursor = conn.cursor()
        query = """
        UPDATE registrations SET
            domain_type=%s, industry_reg_type=%s, vendor_name=%s, website=%s, industry_type=%s, contact_no=%s,
            cin_no=%s, llpin_no=%s, tan_no=%s, gst=%s, gst_certificate=%s, pan=%s, pan_certificate=%s, msme_no=%s,
            billing_address_type=%s, billing_line1=%s, billing_line2=%s, billing_line3=%s,
            billing_city=%s, billing_state=%s, billing_pin=%s,
            shipping_address_type=%s, shipping_line1=%s, shipping_line2=%s, shipping_line3=%s,
            shipping_city=%s, shipping_state=%s, shipping_pin=%s,
            bank_name=%s, branch_name=%s, account_no=%s, account_type=%s, ifsc=%s, micr=%s,
            it_contact_name=%s, it_designation=%s, it_email=%s, it_mobile=%s, it_landline=%s,
            purchase_contact_name=%s, purchase_designation=%s, purchase_email=%s, purchase_mobile=%s, purchase_landline=%s,
            accounts_contact_name=%s, accounts_designation=%s, accounts_email=%s, accounts_mobile=%s, accounts_landline=%s,
            finance_contact_name=%s, finance_designation=%s, finance_email=%s, finance_mobile=%s, finance_landline=%s,
            declarant_name=%s, declarant_designation=%s, declarant_email=%s, declarant_date=%s, declarant_signature=%s
        WHERE id=%s
        """
        values = (
            data.get('domainType'), data.get('industryRegType'), data.get('vendorName'), data.get('website'),
            data.get('industry'), data.get('contactNo'),
            data.get('cin'), data.get('llpin'), data.get('tan'), data.get('gst'), data.get('gstCert'),
            data.get('pan'), data.get('panCert'), data.get('msme'),
            data.get('billType'), data.get('billLine1'), data.get('billLine2'), data.get('billLine3'),
            data.get('billCity'), data.get('billState'), data.get('billPin'),
            data.get('shipType'), data.get('shipLine1'), data.get('shipLine2'), data.get('shipLine3'),
            data.get('shipCity'), data.get('shipState'), data.get('shipPin'),
            data.get('bankName'), data.get('branchName'), data.get('accountNo'),
            data.get('accountType'), data.get('ifsc'), data.get('micr'),
            data.get('itName'), data.get('itDesig'), data.get('itEmail'), data.get('itMobile'), data.get('itLandline'),
            data.get('purName'), data.get('purDesig'), data.get('purEmail'), data.get('purMobile'), data.get('purLandline'),
            data.get('accName'), data.get('accDesig'), data.get('accEmail'), data.get('accMobile'), data.get('accLandline'),
            data.get('finName'), data.get('finDesig'), data.get('finEmail'), data.get('finMobile'), data.get('finLandline'),
            data.get('declName'), data.get('declDesig'), data.get('declEmail'), data.get('declDate'), data.get('signature'),
            registration_id
        )
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── Generate PDF ──────────────────────────────────────────────────────────────

@app.route('/generate-pdf/<int:registration_id>')
def generate_pdf(registration_id):
    if session.get('verified_registration_id') != registration_id:
        return redirect(url_for('home'))
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM registrations WHERE id = %s", (registration_id,))
        data = dict(cursor.fetchone())
        cursor.close()
        conn.close()
        if not data:
            return jsonify({'error': 'Registration not found'}), 404
        if data['declarant_date']:
            data['declarant_date'] = data['declarant_date'].strftime('%d-%m-%Y')
        html_content = render_template('pdf_template.html', data=data, itcg_logo=get_itcg_logo_b64())
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            pdfkit.from_string(html_content, tmp_file.name, configuration=PDFKIT_CONFIG, options=PDF_OPTIONS)
            tmp_file_path = tmp_file.name
        filename = f"ITCG_Registration_{data.get('registration_number', registration_id)}.pdf"
        return send_file(tmp_file_path, as_attachment=True, download_name=filename, mimetype='application/pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Confirm Registration ──────────────────────────────────────────────────────

@app.route('/api/confirm-registration/<int:registration_id>', methods=['POST'])
def confirm_registration(registration_id):
    if session.get('verified_registration_id') != registration_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    try:
        conn = get_db_connection()
        declarant_email = None
        if conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT declarant_email FROM registrations WHERE id = %s", (registration_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if row:
                declarant_email = (row.get('declarant_email') or '').strip()

        if not declarant_email:
            return jsonify({'success': False, 'error': 'Declarant email not found'}), 400

        if send_confirmation_email(declarant_email, registration_id):
            return jsonify({
                'success': True,
                'message': f'Confirmation sent to {declarant_email} (accountant notified separately)'
            })
        return jsonify({'success': False, 'error': 'Failed to send confirmation email'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


create_tables()

if __name__ == '__main__':
    app.run(debug=True, port=5000)