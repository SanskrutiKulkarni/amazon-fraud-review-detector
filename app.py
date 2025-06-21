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
    """Detect if content is AI-generated using Gemini"""
    try:
        # Initialize the model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""Analyze this text and determine if it was AI-generated. 
        Respond ONLY with 'AI' or 'Human':
        Text: \"\"\"{text[:1000]}\"\"\""""
        
        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                temperature=0.0,  # For deterministic responses
                max_output_tokens=1  # We only need one word
            )
        )
        
        decision = response.text.strip().upper()
        
        if decision == 'AI':
            return True, 0.9, "AI-generated (Gemini Detection)"
        elif decision == 'UNCERTAIN':  # If you want to handle uncertain cases
            return True, 0.6, "Possibly AI-generated (Gemini)"
        else:
            return False, 0.1, "Human-written"
            
    except Exception as e:
        print(f"Gemini Detection Error: {e}")
        # Fallback to pattern matching
        ai_patterns = [
            r"\bas an ai\b", r"\blanguage model\b", 
            r"\bartificial intelligence\b", r"\baccording to my (knowledge|training data)\b",
            r"\bas a (large )?language model\b", r"\bopenai\b", r"\bchatgpt\b"
        ]
        for pattern in ai_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True, 0.85, f"AI-generated (pattern: {pattern})"
        return False, 0.0, "Human-written (fallback)"

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

# --- API Endpoints ---

@app.route('/submit-review', methods=['POST'])
def submit_review():
    data = request.json
    text = data.get('text', '').strip()
    ip = request.remote_addr or "127.0.0.1"
    user_agent = request.headers.get('User-Agent', '')

    if not text:
        return jsonify({'status': 'error', 'message': 'Review text required'}), 400

    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()

    # Layer 1: AI Detection
    is_ai, ai_conf, ai_reason = detect_ai_content(text)
    if is_ai:
        try:
            c.execute("""INSERT INTO reviews 
                      (text, ip, user_agent, status, review_status, reason, confidence, timestamp, last_updated)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (text, ip, user_agent, 'blocked', 'auto_rejected',
                       ai_reason, ai_conf, datetime.now(), datetime.now()))
            conn.commit()
            return jsonify({
                'status': 'blocked',
                'reason': ai_reason,
                'confidence': ai_conf,
                'layer': 1
            })
        finally:
            conn.close()

    # Layer 2: Paid/Incentivized Detection
    # is_paid, paid_conf, paid_reason = detect_paid_behavior(ip, text)
    is_paid, paid_conf, paid_reason = detect_paid_review(text)
    if is_paid:
        try:
            c.execute("""INSERT INTO reviews VALUES 
                      (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (text, ip, user_agent, 'quarantined', 'pending',
                       paid_reason, paid_conf, datetime.now(), datetime.now()))
            conn.commit()
            return jsonify({
                'status': 'quarantined',
                'reason': paid_reason,
                'confidence': paid_conf,
                'layer': 2,
                'needs_review': True
            })
        finally:
            conn.close()

    # Layer 3: Bot Detection
    is_bot, bot_conf, bot_reason = detect_bot(ip, user_agent)
    if is_bot:
        try:
            # Insert into both tables
            c.execute("""INSERT INTO bot_detections VALUES 
                      (NULL, ?, ?, ?, ?, ?, ?)""",
                      (ip, user_agent, True, bot_conf, bot_reason, datetime.now()))
            c.execute("""INSERT INTO reviews VALUES 
                      (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (text, ip, user_agent, 'blocked', 'auto_rejected',
                       bot_reason, bot_conf, datetime.now(), datetime.now()))
            conn.commit()
            return jsonify({
                'status': 'blocked',
                'reason': bot_reason,
                'confidence': bot_conf,
                'layer': 3
            })
        finally:
            conn.close()

    # If all checks pass - approved review
    try:
        c.execute("""INSERT INTO reviews VALUES 
                  (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (text, ip, user_agent, 'published', 'auto_approved',
                   'Genuine review', 1.0, datetime.now(), datetime.now()))
        conn.commit()
        return jsonify({
            'status': 'published',
            'badge': 'verified'
        })
    finally:
        conn.close()


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
    
    c.execute("SELECT status, COUNT(*) FROM reviews GROUP BY status")
    status_counts = dict(c.fetchall())
    
    c.execute("SELECT reason, COUNT(*) FROM reviews WHERE status != 'published' GROUP BY reason")
    rejection_reasons = dict(c.fetchall())
    
    conn.close()
    
    return jsonify({
        'status_distribution': status_counts,
        'rejection_reasons': rejection_reasons
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