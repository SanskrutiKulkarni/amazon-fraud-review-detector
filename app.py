import os
import sqlite3
import requests
import re
import google.generativeai as genai
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
    
    # Reviews Table
    c.execute('''CREATE TABLE IF NOT EXISTS reviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 text TEXT,
                 ip TEXT,
                 user_agent TEXT,
                 status TEXT,
                 reason TEXT,
                 confidence REAL,
                 timestamp DATETIME)''')
    
    # Bot Detections Table - UPDATED SCHEMA
    c.execute('''CREATE TABLE IF NOT EXISTS bot_detections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 ip TEXT,
                 user_agent TEXT,
                 is_bot BOOLEAN,
                 confidence REAL,
                 details TEXT,  -- Changed from 'reason' to 'details'
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

def detect_ai_content(text):
    """Detect if content is AI-generated using Gemini + pattern-based strategy"""
    
    # --- Strategy 1: Gemini LLM-based Detection ---
    try:
        prompt = f"""
You are an AI content detection expert. Analyze the following text and respond ONLY with one of these three options: "AI-generated", "Human-written", or "Uncertain".
Text: \"\"\"{text[:1000]}\"\"\"
Answer:
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0,
                thinking_config=types.ThinkingConfig(thinking_budget=1024)
            )
        )

        decision = response.text.strip().lower()

        if "ai-generated" in decision:
            return True, 0.9, "AI-generated (Gemini)"
        elif "uncertain" in decision:
            return True, 0.6, "Possibly AI-generated (Gemini)"
        # If "Human-written", fall through to pattern matching
    except Exception as e:
        print(f"Gemini Detection Error: {e}")

    # --- Strategy 2: Pattern Matching Fallback ---
    ai_patterns = [
        r"\bas an ai\b", r"\blanguage model\b", 
        r"\bartificial intelligence\b", r"\baccording to my (knowledge|training data)\b",
        r"\bas a (large )?language model\b", r"\bopenai\b", r"\bchatgpt\b"
    ]
    for pattern in ai_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True, 0.85, f"AI-generated (pattern: {pattern})"

    return False, 0.0, "Human-written"

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
        c.execute("INSERT INTO reviews VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)",
                 (text, ip, user_agent, 'blocked', ai_reason, ai_conf, datetime.now()))
        conn.commit()
        conn.close()
        return jsonify({
            'status': 'blocked',
            'reason': ai_reason,
            'confidence': ai_conf,
            'layer': 1
        })

    # Layer 2: Paid Review
    is_paid, paid_conf, paid_reason = detect_paid_review(text)
    if is_paid:
        c.execute("INSERT INTO reviews VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)",
                 (text, ip, user_agent, 'quarantined', paid_reason, paid_conf, datetime.now()))
        conn.commit()
        conn.close()
        return jsonify({
            'status': 'quarantined',
            'reason': paid_reason,
            'confidence': paid_conf,
            'layer': 2
        })

    # Layer 3: Bot Detection
    is_bot, bot_conf, bot_reason = detect_bot(ip, user_agent)
    if is_bot:
        c.execute("INSERT INTO bot_detections VALUES (NULL, ?, ?, ?, ?, ?, ?)",
             (ip, user_agent, True, bot_conf, bot_reason, datetime.now()))
        c.execute("INSERT INTO reviews VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)",
                 (text, ip, user_agent, 'blocked', bot_reason, bot_conf, datetime.now()))
        conn.commit()
        conn.close()
        return jsonify({
            'status': 'blocked',
            'reason': bot_reason,
            'confidence': bot_conf,
            'layer': 3
        })

    # Approved Review
    c.execute("INSERT INTO reviews VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)",
             (text, ip, user_agent, 'published', 'Genuine review', 1.0, datetime.now()))
    conn.commit()
    conn.close()
    return jsonify({
        'status': 'published',
        'badge': 'verified'
    })

@app.route('/get-quarantined')
def get_quarantined():
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("SELECT id, text, reason, confidence FROM reviews WHERE status != 'published' ORDER BY timestamp DESC")
    results = [dict(zip(['id', 'text', 'reason', 'confidence'], row)) for row in c.fetchall()]
    conn.close()
    return jsonify(results)

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