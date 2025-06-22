# Truvo - AI-Powered Review Moderation System

![Truvo Logo](https://via.placeholder.com/150x50?text=Truvo) *(Add your actual logo here)*

A comprehensive AI-powered review moderation system that automatically detects and filters suspicious reviews using multi-layered verification.

## Features

### 🛡️ Multi-Stage Verification Pipeline
- **AI Content Detection** - Identifies machine-generated reviews using Gemini AI
- **Bot Detection** - Analyzes IP reputation and user agent patterns
- **Paid Review Detection** - Flags incentivized reviews
- **CAPTCHA Verification** - Human verification with reCAPTCHA v3
- **IP Analysis** - Tracks suspicious activity patterns

### 🧠 Smart Quarantine System
- Confidence scoring for each detection
- Manual review workflow for uncertain cases
- Granular classification of suspicious content

### 📊 Real-Time Analytics Dashboard
- Visual moderation statistics
- Detection type breakdowns
- Daily activity trends
- Quarantine management interface

## Technology Stack

### Backend
- Python 3.9+
- Flask (Web Framework)
- PostgreSQL (Database)
- Google Generative AI (AI Detection)
- IPQualityScore (IP/Bot Detection)

### Frontend
- HTML5/CSS3
- Chart.js (Data Visualization)
- Vanilla JavaScript

### APIs Used
- Google reCAPTCHA v3
- IPQualityScore API (Optional)
- Hugging Face API (Secondary AI detection)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/truvo.git
   cd truvo
   
2. **Set up environment variables**
   Create a .env file with:
   ```bash
   DATABASE_URL=your_postgres_connection_string
   GEMINI_API_KEY=your_google_ai_key
   RECAPTCHA_SECRET_KEY=your_recaptcha_key
   IPQS_KEY=your_ipqualityscore_key (optional)
   FLASK_SECRET_KEY=your_secret_key

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt

4. **Run the application**
    ```bash
    python app.py

##  Usage
**Access Endpoints**
- Web Interface: http://localhost:5000

- API Base URL: http://localhost:5000/api

**Key API Endpoints**
Endpoint	Method	Description
- /submit-review:	POST	(Submit a review for moderation)
- /get-quarantined:	GET	(Get reviews needing manual approval)
- /approve-review/<id>:	(POST	Approve a quarantined review)
- /stats:	GET	9Get moderation statistics)

**AI Content Detection**
- Primary check using Gemini 1.5 Pro
- Secondary verification with Hugging Face API
- Regex pattern matching for known AI phrases
- Behavioral analysis (lexical diversity, personal pronouns)

**Bot Detection**
- IPQualityScore reputation check
- User agent analysis
- Activity pattern monitoring
- Cloud provider IP detection

**Database Schema**
Main Tables:
- reviews - Stores all review submissions and moderation status

- bot_detections - Tracks identified bot activity

- ip_activity - Logs IP address actions

- users - Administrator accounts
