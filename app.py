import os
import sqlite3
import requests
import re
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Initialize Database
def init_db():
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    
    # Reviews Table with all columns you're using
    c.execute('''CREATE TABLE IF NOT EXISTS reviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 text TEXT,
                 ip TEXT,
                 user_agent TEXT,
                 status TEXT,
                 review_status TEXT,
                 reason TEXT,
                 confidence REAL,
                 timestamp DATETIME,
                 last_updated DATETIME)''')
    
    # Bot Detections Table
    c.execute('''CREATE TABLE IF NOT EXISTS bot_detections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 ip TEXT,
                 user_agent TEXT,
                 is_bot BOOLEAN,
                 confidence REAL,
                 details TEXT,
                 timestamp DATETIME)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS ip_activity
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 ip TEXT NOT NULL,
                 timestamp DATETIME NOT NULL,
                 user_agent TEXT,
                 action TEXT)''')
    
    conn.commit()
    conn.close()

init_db()

# --- Detection Services ---

# def detect_ai_content(text):
#     """Enhanced AI detection with multiple strategies"""
#     # Hugging Face API
#     if os.getenv('HF_API_KEY'):
#         try:
#             API_URL = "https://api-inference.huggingface.co/models/Hello-SimpleAI/chatgpt-detector-roberta"
#             headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
#             response = requests.post(API_URL, headers=headers, json={"inputs": text[:1000]}, timeout=5)
            
#             if response.status_code == 200:
#                 result = response.json()
#                 if isinstance(result, list):
#                     confidence = result[0][0]['score']
#                     if confidence > float(os.getenv('AI_CONFIDENCE_THRESHOLD', 0.7)):
#                         return True, confidence, "AI-generated (Hugging Face)"
#         except Exception as e:
#             print(f"AI Detection API Error: {e}")

#     # Pattern Matching
#     ai_patterns = [
#         r"\bas an ai\b", r"\blanguage model\b", 
#         r"\bartificial intelligence\b", r"\baccording to my (knowledge|training data)\b",
#         r"\bas a (large )?language model\b", r"\bopenai\b", r"\bchatgpt\b"
#     ]
#     for pattern in ai_patterns:
#         if re.search(pattern, text, re.IGNORECASE):
#             return True, 0.85, f"AI-generated (pattern: {pattern})"

#     return False, 0.0, ""


# Configure the API key (make sure it's in your .env file)
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def detect_ai_content(text):
    """Detect AI content and properly route to quarantine when uncertain"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""Analyze this text for AI-generation indicators:
1. Overly perfect grammar/syntax
2. Generic/impersonal tone
3. Lack of specific details
4. Known AI phrases

Respond ONLY with:
- 'AI' for definite AI content
- 'QUARANTINE' for suspicious but uncertain
- 'HUMAN' for definite human content

Text: \"\"\"{text[:2000]}\"\"\""""
        
        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                temperature=0.1,
                max_output_tokens=1
            )
        )
        
        decision = response.text.strip().upper()
        
        if decision == 'AI':
            return True, 0.9, "Definite AI-generated content", 'blocked', 'auto_rejected'
        elif decision == 'QUARANTINE':
            return True, 0.65, "Suspected AI content - needs human review", 'quarantined', 'pending'
        else:
            return False, 0.1, "Human-written content", 'published', 'auto_approved'
            
    except Exception as e:
        print(f"AI Detection Error: {str(e)}")
        # Fallback checks
        if len(text) > 300 and len(set(text.split())) < len(text.split())/3:
            return True, 0.7, "Possible AI (repetitive content)", 'quarantined', 'pending'
        return False, 0.2, "Human (fallback check)", 'published', 'auto_approved'

# def detect_bot(ip, user_agent=""):
#     """Advanced bot detection using IPQualityScore + behavioral analysis"""
#     # Skip localhost
#     if ip in ("127.0.0.1", "localhost"):
#         return False, 0.0, ""
    
#     # IPQualityScore API
#     if os.getenv('IPQS_KEY'):
#         try:
#             params = {
#                 'strictness': 1,
#                 'allow_public_access_points': 'true',
#                 'fast': 'false'
#             }
#             response = requests.get(
#                 f"https://www.ipqualityscore.com/api/json/ip/{os.getenv('IPQS_KEY')}/{ip}",
#                 params=params,
#                 timeout=5
#             )
#             data = response.json()
            
#             if data.get('success', False):
#                 bot_score = data.get('bot_score', 0)/100
#                 if data.get('bot_status', False) or bot_score >= float(os.getenv('BOT_CONFIDENCE_THRESHOLD', 0.85)):
#                     details = []
#                     if data.get('is_crawler'): details.append("crawler")
#                     if data.get('is_bot'): details.append("automated")
#                     if data.get('proxy'): details.append("proxy")
#                     return True, bot_score, f"Bot ({', '.join(details)})"
#         except Exception as e:
#             print(f"IPQS API Error: {e}")

#     # Behavioral Analysis
#     suspicious = []
    
#     # User Agent Analysis
#     if not user_agent:
#         suspicious.append("missing UA")
#     else:
#         ua = user_agent.lower()
#         if any(x in ua for x in ['bot', 'crawler', 'spider', 'python', 'java', 'curl']):
#             suspicious.append("suspicious UA")

#     # IP Analysis
#     if any(x in ip.lower() for x in ['23.', '54.', 'aws', 'google', 'azure']):
#         suspicious.append("cloud IP")

#     if suspicious:
#         return True, 0.7, f"Bot-like ({', '.join(suspicious)})"

#     return False, 0.0, ""

# ... (previous imports and app setup) ...

def detect_bot(ip, user_agent=""):
    """Advanced bot detection using IPQualityScore + behavioral analysis"""
    # Skip localhost
    if ip in ("127.0.0.1", "localhost"):
        return False, 0.0, ""
    
    # IPQualityScore API
    if os.getenv('IPQS_KEY'):
        try:
            params = {
                'strictness': 1,
                'allow_public_access_points': 'true',
                'fast': 'false'
            }
            response = requests.get(
                f"https://www.ipqualityscore.com/api/json/ip/{os.getenv('IPQS_KEY')}/{ip}",
                params=params,
                timeout=5
            )
            data = response.json()
            
            if data.get('success', False):
                bot_score = data.get('bot_score', 0)/100
                if data.get('bot_status', False) or bot_score >= float(os.getenv('BOT_CONFIDENCE_THRESHOLD', 0.85)):
                    details = []
                    if data.get('is_crawler'): details.append("crawler")
                    if data.get('is_bot'): details.append("automated")
                    if data.get('proxy'): details.append("proxy")
                    return True, bot_score, f"Bot ({', '.join(details)})"
        except Exception as e:
            print(f"IPQS API Error: {e}")

    # Behavioral Analysis
    suspicious = []
    
    # User Agent Analysis
    if not user_agent:
        suspicious.append("missing UA")
    else:
        ua = user_agent.lower()
        if any(x in ua for x in ['bot', 'crawler', 'spider', 'python', 'java', 'curl']):
            suspicious.append("suspicious UA")

    # IP Analysis
    if any(x in ip.lower() for x in ['23.', '54.', 'aws', 'google', 'azure']):
        suspicious.append("cloud IP")

    if suspicious:
        return True, 0.7, f"Bot-like ({', '.join(suspicious)})"

    return False, 0.0, ""

def detect_paid_review(text):
    """Comprehensive paid review detection"""
    paid_patterns = [
        r"\breceived (this )?(product|item) (for free|as a gift)\b",
        r"\bin exchange for (my )?(honest|unbiased) review\b",
        r"\b(discount|compensation) (for|in exchange for) (a|my) review\b",
        r"\bwas (provided|given) (this )?(product|item) (to test|for review)\b"
    ]
    
    for pattern in paid_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True, 0.95, f"Paid review (pattern: {pattern})"
    
    # Generic praise detection
    if len(text) < 50 and len(re.findall(r"\b(excellent|great|awesome|perfect)\b", text, re.IGNORECASE)) >= 2:
        return True, 0.8, "Paid review (generic praise)"
    
    return False, 0.0, ""

def get_client_ip():
    """Get real client IP address, even behind proxy."""
    if request.headers.get('X-Forwarded-For'):
        # Handle cases where app is behind a proxy
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        ip = request.remote_addr
    return ip

def verify_captcha(token, ip):
    url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {
        'secret': os.getenv("RECAPTCHA_SECRET_KEY"),  # or hardcode for testing
        'response': token,
        'remoteip': ip
    }
    try:
        response = requests.post(url, data=payload, timeout=5)
        result = response.json()
        return result.get("success", False)
    except Exception as e:
        print("CAPTCHA Verification Error:", e)
        return False
    
def check_ip_activity(ip):
    """Check if IP is posting too frequently"""
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    
    # Get submissions in last hour
    c.execute("""SELECT COUNT(*) FROM ip_activity 
              WHERE ip = ? AND timestamp > datetime('now', '-1 hour')""", (ip,))
    count = c.fetchone()[0]
    
    # Get all submissions from this IP
    c.execute("""SELECT COUNT(DISTINCT strftime('%Y-%m-%d', timestamp)) 
              FROM ip_activity WHERE ip = ?""", (ip,))
    days_active = c.fetchone()[0] or 1
    
    # Calculate average per day
    c.execute("""SELECT COUNT(*) FROM ip_activity WHERE ip = ?""", (ip,))
    total = c.fetchone()[0]
    avg_per_day = total / days_active
    
    conn.close()
    
    # Thresholds (adjust as needed)
    if count > 5:  # More than 5 in 1 hour
        return True, "Excessive hourly submissions"
    if avg_per_day > 3:  # More than 3 per day average
        return True, "Consistent daily spamming"
    return False, ""

# --- API Endpoints ---

@app.route('/submit-review', methods=['POST'])
def submit_review():
    # Initial setup
    data = request.json
    text = data.get('text', '').strip()
    captcha_token = data.get('captcha', '')
    ip = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')
    timestamp = datetime.now()
    
    print(f"[Review Submission] IP: {ip}, User-Agent: {user_agent}")

    # Initialize database connection
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    
    # Log submission attempt
    c.execute("""INSERT INTO ip_activity 
              (ip, timestamp, user_agent, action) 
              VALUES (?, ?, ?, ?)""",
              (ip, timestamp, user_agent, 'submission_attempt'))
    conn.commit()

    # --- Sequential Validation Checks ---

    # Check 1: Basic Validation
    if not text:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Review text required'}), 400

    # Check 2: IP Activity Patterns
    is_suspicious, reason = check_ip_activity(ip)
    if is_suspicious:
        c.execute("""INSERT INTO reviews 
                  (text, ip, user_agent, status, review_status, reason, confidence, timestamp, last_updated)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (text, ip, user_agent, 'blocked', 'auto_rejected',
                   f"Suspicious activity: {reason}", 0.95, timestamp, timestamp))
        conn.commit()
        conn.close()
        return jsonify({
            'status': 'blocked',
            'reason': f"Suspicious posting pattern: {reason}",
            'confidence': 0.95
        }), 403

    # Check 3: CAPTCHA Verification
    if not verify_captcha(captcha_token, ip):
        c.execute("""INSERT INTO reviews 
                  (text, ip, user_agent, status, review_status, reason, confidence, timestamp, last_updated)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (text, ip, user_agent, 'blocked', 'auto_rejected',
                   "Failed CAPTCHA verification", 0.9, timestamp, timestamp))
        conn.commit()
        conn.close()
        return jsonify({'status': 'error', 'message': 'CAPTCHA verification failed'}), 400

    # Check 4: AI Content Detection
    is_ai, ai_conf, ai_reason, ai_status, ai_review_status = detect_ai_content(text)
    if is_ai:
        c.execute("""INSERT INTO reviews 
                  (text, ip, user_agent, status, review_status, reason, confidence, timestamp, last_updated)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (text, ip, user_agent, ai_status, ai_review_status,
                   ai_reason, ai_conf, timestamp, timestamp))
        conn.commit()
        conn.close()
        
        if ai_status == 'quarantined':
            return jsonify({
                'status': 'quarantined',
                'reason': ai_reason,
                'confidence': ai_conf,
                'needs_review': True
            })
        else:
            return jsonify({
                'status': 'blocked',
                'reason': ai_reason,
                'confidence': ai_conf
            })

    # Check 5: Paid/Incentivized Review Detection
    is_paid, paid_conf, paid_reason = detect_paid_review(text)
    if is_paid:
        # For paid reviews, we always quarantine for human review
        c.execute("""INSERT INTO reviews 
                  (text, ip, user_agent, status, review_status, reason, confidence, timestamp, last_updated)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (text, ip, user_agent, 'quarantined', 'pending',
                   paid_reason, paid_conf, timestamp, timestamp))
        conn.commit()
        conn.close()
        return jsonify({
            'status': 'quarantined',
            'reason': paid_reason,
            'confidence': paid_conf,
            'needs_review': True
        })

    # Check 6: Bot Detection
    is_bot, bot_conf, bot_reason = detect_bot(ip, user_agent)
    if is_bot:
        # Insert into both tables
        c.execute("""INSERT INTO bot_detections VALUES 
                  (NULL, ?, ?, ?, ?, ?, ?)""",
                  (ip, user_agent, True, bot_conf, bot_reason, timestamp))
        c.execute("""INSERT INTO reviews 
                  (text, ip, user_agent, status, review_status, reason, confidence, timestamp, last_updated)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (text, ip, user_agent, 'blocked', 'auto_rejected',
                   bot_reason, bot_conf, timestamp, timestamp))
        conn.commit()
        conn.close()
        return jsonify({
            'status': 'blocked',
            'reason': bot_reason,
            'confidence': bot_conf
        })

    # If all checks pass - approved review
    c.execute("""INSERT INTO reviews 
              (text, ip, user_agent, status, review_status, reason, confidence, timestamp, last_updated)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (text, ip, user_agent, 'published', 'auto_approved',
               'Genuine review', 1.0, timestamp, timestamp))
    conn.commit()
    conn.close()
    
    return jsonify({
        'status': 'published',
        'badge': 'verified'
    })

@app.route('/get-quarantined')
def get_quarantined():
    """Get only reviews needing human review"""
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("""SELECT id, text, reason, confidence, timestamp 
              FROM reviews 
              WHERE status = 'quarantined' AND review_status = 'pending'
              ORDER BY timestamp DESC""")
    results = [dict(zip(['id', 'text', 'reason', 'confidence', 'timestamp'], row)) 
              for row in c.fetchall()]
    conn.close()
    return jsonify(results)

@app.route('/approve-review/<int:review_id>', methods=['POST'])
def approve_review(review_id):
    """Approve a quarantined review"""
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("""UPDATE reviews 
              SET status = 'published', 
                  review_status = 'approved',
                  last_updated = ?
              WHERE id = ?""", (datetime.now(), review_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/reject-review/<int:review_id>', methods=['POST'])
def reject_review(review_id):
    """Reject a quarantined review"""
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("""UPDATE reviews 
              SET status = 'blocked', 
                  review_status = 'rejected',
                  last_updated = ?
              WHERE id = ?""", (datetime.now(), review_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# @app.route('/bot-analytics')
# def bot_analytics():
#     conn = sqlite3.connect('reviews.db')
#     c = conn.cursor()
    
#     c.execute("SELECT COUNT(*) FROM bot_detections WHERE is_bot = 1")
#     total_bots = c.fetchone()[0]
    
#     c.execute("SELECT COUNT(DISTINCT ip) FROM bot_detections")
#     unique_ips = c.fetchone()[0]
    
#     c.execute("SELECT reason, COUNT(*) FROM bot_detections GROUP BY reason")
#     detection_types = dict(c.fetchall())
    
#     conn.close()
    
#     return jsonify({
#         'total_bots_blocked': total_bots,
#         'unique_bot_ips': unique_ips,
#         'detection_types': detection_types
#     })

@app.route('/bot-analytics')
def bot_analytics():
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM bot_detections WHERE is_bot = 1")
    total_bots = c.fetchone()[0]
    
    c.execute("SELECT COUNT(DISTINCT ip) FROM bot_detections")
    unique_ips = c.fetchone()[0]
    
    c.execute("SELECT details, COUNT(*) FROM bot_detections GROUP BY details")  # Changed to 'details'
    detection_types = dict(c.fetchall())
    
    conn.close()
    
    return jsonify({
        'total_bots_blocked': total_bots,
        'unique_bot_ips': unique_ips,
        'detection_types': detection_types
    })

@app.route('/stats')
def stats():
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    
    # Status distribution
    c.execute("""
        SELECT 
            SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as approved,
            SUM(CASE WHEN status = 'quarantined' THEN 1 ELSE 0 END) as quarantined,
            SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked,
            COUNT(*) as total
        FROM reviews
    """)
    status_counts = dict(zip(['approved', 'quarantined', 'blocked', 'total'], c.fetchone()))
    
    # Rejection reasons breakdown
    c.execute("""
        SELECT 
            SUM(CASE WHEN reason LIKE '%AI%' THEN 1 ELSE 0 END) as ai_rejections,
            SUM(CASE WHEN reason LIKE '%Paid%' THEN 1 ELSE 0 END) as paid_rejections,
            SUM(CASE WHEN reason LIKE '%Bot%' THEN 1 ELSE 0 END) as bot_rejections,
            SUM(CASE WHEN reason LIKE '%CAPTCHA%' THEN 1 ELSE 0 END) as captcha_rejections,
            SUM(CASE WHEN reason LIKE '%Suspicious activity%' THEN 1 ELSE 0 END) as activity_rejections
        FROM reviews 
        WHERE status != 'published'
    """)
    rejection_reasons = dict(zip(
        ['ai_rejections', 'paid_rejections', 'bot_rejections', 'captcha_rejections', 'activity_rejections'],
        c.fetchone()
    ))
    
    # Daily activity
    c.execute("""
        SELECT 
            strftime('%Y-%m-%d', timestamp) as day,
            SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as approved,
            SUM(CASE WHEN status = 'quarantined' THEN 1 ELSE 0 END) as quarantined,
            SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked
        FROM reviews
        WHERE timestamp > date('now', '-7 days')
        GROUP BY day
        ORDER BY day
    """)
    daily_activity = [dict(zip(['day', 'approved', 'quarantined', 'blocked'], row)) 
                     for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({
        'status_distribution': status_counts,
        'rejection_reasons': rejection_reasons,
        'daily_activity': daily_activity
    })

@app.route('/dashboard-data')
def dashboard_data():
    # Get all stats in one request
    stats_response = stats().get_json()
    
    # Add quarantined reviews
    quarantined = get_quarantined().get_json()
    
    # Add bot analytics
    bot_stats = bot_analytics().get_json()
    
    return jsonify({
        'stats': stats_response,
        'quarantined': quarantined,
        'bot_stats': bot_stats
    })

# Frontend Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)