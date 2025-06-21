# Truvo Review Moderation System
A comprehensive AI-powered review moderation system that automatically detects and filters suspicious reviews using multi-layered verification.

## Features

- **Multi-Stage Verification Pipeline**
  - IP reputation analysis
  - CAPTCHA verification
  - AI-generated content detection
  - Paid/incentivized review detection
  - Bot activity detection

- **Smart Quarantine System**
  - Automatic flagging of uncertain reviews
  - Confidence scoring for each detection
  - Manual review workflow

- **Real-Time Analytics Dashboard**
  - Visual moderation statistics
  - Detection type breakdowns
  - Daily activity trends
  - Quarantine management interface

## Technology Stack

**Backend:**
- Python 3.9+
- Flask (Web Framework)
- SQLite (Database)
- Google Generative AI (AI Detection)
- IPQualityScore (IP/Bot Detection)

**Frontend:**
- HTML5/CSS3
- Chart.js (Data Visualization)
- Vanilla JavaScript

**APIs Used:**
- Google reCAPTCHA v3
- IPQualityScore API (Optional)

## Running

**Command:**
- python app.py 

**Run on port:** 
- http://127.0.0.1:5000
