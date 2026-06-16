-- ITCG Vendor Registration Database Schema
-- PostgreSQL Version
-- --------------------------------------------------------

-- Table: otp_verification
-- --------------------------------------------------------
DROP TABLE IF EXISTS otp_verification;
CREATE TABLE otp_verification (
  id         SERIAL PRIMARY KEY,
  email      VARCHAR(255) NOT NULL,
  otp        VARCHAR(6) NOT NULL,
  purpose    VARCHAR(50) DEFAULT 'form_submit',
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_email   ON otp_verification (email);
CREATE INDEX idx_expires ON otp_verification (expires_at);

-- --------------------------------------------------------
-- Table: registrations
-- --------------------------------------------------------
DROP TABLE IF EXISTS registrations;
CREATE TABLE registrations (
  id                      SERIAL PRIMARY KEY,
  registration_number     VARCHAR(50)  DEFAULT NULL,
  domain_type             VARCHAR(50)  DEFAULT NULL,
  industry_reg_type       VARCHAR(50)  DEFAULT NULL,
  vendor_name             VARCHAR(255) DEFAULT NULL,
  website                 VARCHAR(255) DEFAULT NULL,
  industry_type           VARCHAR(100) DEFAULT NULL,
  contact_no              VARCHAR(50)  DEFAULT NULL,
  cin_no                  VARCHAR(100) DEFAULT NULL,
  llpin_no                VARCHAR(100) DEFAULT NULL,
  tan_no                  VARCHAR(100) DEFAULT NULL,
  gst                     VARCHAR(100) DEFAULT NULL,
  gst_certificate         VARCHAR(10)  DEFAULT NULL,
  pan                     VARCHAR(100) DEFAULT NULL,
  pan_certificate         VARCHAR(10)  DEFAULT NULL,
  msme_no                 VARCHAR(100) DEFAULT NULL,
  billing_address_type    VARCHAR(100) DEFAULT NULL,
  billing_line1           TEXT,
  billing_line2           TEXT,
  billing_line3           TEXT,
  billing_city            VARCHAR(100) DEFAULT NULL,
  billing_state           VARCHAR(100) DEFAULT NULL,
  billing_pin             VARCHAR(50)  DEFAULT NULL,
  shipping_address_type   VARCHAR(100) DEFAULT NULL,
  shipping_line1          TEXT,
  shipping_line2          TEXT,
  shipping_line3          TEXT,
  shipping_city           VARCHAR(100) DEFAULT NULL,
  shipping_state          VARCHAR(100) DEFAULT NULL,
  shipping_pin            VARCHAR(50)  DEFAULT NULL,
  bank_name               VARCHAR(255) DEFAULT NULL,
  branch_name             VARCHAR(255) DEFAULT NULL,
  account_no              VARCHAR(100) DEFAULT NULL,
  account_type            VARCHAR(100) DEFAULT NULL,
  ifsc                    VARCHAR(50)  DEFAULT NULL,
  micr                    VARCHAR(50)  DEFAULT NULL,
  it_contact_name         VARCHAR(255) DEFAULT NULL,
  it_designation          VARCHAR(255) DEFAULT NULL,
  it_email                VARCHAR(255) DEFAULT NULL,
  it_mobile               VARCHAR(50)  DEFAULT NULL,
  it_landline             VARCHAR(50)  DEFAULT NULL,
  purchase_contact_name   VARCHAR(255) DEFAULT NULL,
  purchase_designation    VARCHAR(255) DEFAULT NULL,
  purchase_email          VARCHAR(255) DEFAULT NULL,
  purchase_mobile         VARCHAR(50)  DEFAULT NULL,
  purchase_landline       VARCHAR(50)  DEFAULT NULL,
  accounts_contact_name   VARCHAR(255) DEFAULT NULL,
  accounts_designation    VARCHAR(255) DEFAULT NULL,
  accounts_email          VARCHAR(255) DEFAULT NULL,
  accounts_mobile         VARCHAR(50)  DEFAULT NULL,
  accounts_landline       VARCHAR(50)  DEFAULT NULL,
  finance_contact_name    VARCHAR(255) DEFAULT NULL,
  finance_designation     VARCHAR(255) DEFAULT NULL,
  finance_email           VARCHAR(255) DEFAULT NULL,
  finance_mobile          VARCHAR(50)  DEFAULT NULL,
  finance_landline        VARCHAR(50)  DEFAULT NULL,
  declarant_name          VARCHAR(255) DEFAULT NULL,
  declarant_designation   VARCHAR(255) DEFAULT NULL,
  declarant_email         VARCHAR(255) DEFAULT NULL,
  declarant_date          DATE         DEFAULT NULL,
  declarant_signature     VARCHAR(255) DEFAULT NULL,
  created_at              TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);
