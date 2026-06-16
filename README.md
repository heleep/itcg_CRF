# CRF System — ITCG Vendor Registration Portal

A Flask web application for vendor registration with OTP verification and PDF generation.

## Project Structure

```
vendor-reg/
├── app.py                   # Main Flask application (all routes & logic)
├── connection.py            # Reads config from .env — DO NOT edit credentials here
├── .env                     # All credentials (never commit this to GitHub)
├── .gitignore               # Keeps .env and uploads out of version control
├── requirement.txt          # Python dependencies
├── database.sql             # MySQL schema — run once to create tables
├── static/
│   ├── style.css
│   ├── script.js
│   └── Registration_Instructions_Guide.pdf
├── templates/
│   ├── index.html           # Main registration form
│   ├── preview.html         # Review page after OTP verification
│   ├── edit_form.html       # Edit page before final confirmation
│   └── pdf_template.html    # HTML template used to generate PDF
└── uploads/                 # Auto-created — stores uploaded certificates
    ├── GST/
    ├── PAN/
    └── MSME/
```

## Setup Instructions

### 1. Install Python packages
```
pip install -r requirement.txt
```

### 2. Install wkhtmltopdf
- **Windows:** Download from https://wkhtmltopdf.org/downloads.html
- **Linux:** `sudo apt install wkhtmltopdf`

### 3. Create MySQL database
```
mysql -u root -p < database.sql
```

### 4. Configure your .env file
Edit `.env` and fill in your real values:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=itcg_registration2
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your_app_password
...
```

### 5. Run the app
```
python app.py
```
Open http://localhost:5000

## Changing Email Provider
To switch from Gmail to Outlook, update only `.env`:
```
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USERNAME=your@outlook.com
MAIL_PASSWORD=your_outlook_password
```

## Moving Database to Cloud (e.g. AWS RDS)
Update only `.env`:
```
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_USER=admin
DB_PASSWORD=your_rds_password
DB_NAME=itcg_registration2
```
