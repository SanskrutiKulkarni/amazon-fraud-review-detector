import os
# import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import requests
import re
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from flask import Flask, render_template, request, jsonify, redirect, session
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import urllib.parse as urlparse
import socket

load_dotenv()

app = Flask(__name__)
CORS(app)

# def get_db_connection():
#     return psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)

def get_db_connection():    
    # Parse the DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    # For Supabase, you might need to modify the URL scheme
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgres://")
    
    try:
        urlparse.uses_netloc.append("postgres")
        url = urlparse.urlparse(db_url)
        
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

# Initialize Database
# def init_db():
#     # conn = sqlite3.connect('reviews.db')
#     conn = get_db_connection()

#     c = conn.cursor()
    
#     # Reviews Table with all columns you're using
#     c.execute('''CREATE TABLE IF NOT EXISTS reviews
#                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
#                  text TEXT,
#                  ip TEXT,
#                  user_agent TEXT,
#                  status TEXT,
#                  review_status TEXT,
#                  reason TEXT,
#                  confidence REAL,
#                  timestamp DATETIME,
#                  last_updated DATETIME)''')
    
#     # Bot Detections Table
#     c.execute('''CREATE TABLE IF NOT EXISTS bot_detections
#                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
#                  ip TEXT,
#                  user_agent TEXT,
#                  is_bot BOOLEAN,
#                  confidence REAL,
#                  details TEXT,
#                  timestamp DATETIME)''')
    
#     c.execute('''CREATE TABLE IF NOT EXISTS ip_activity
#                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
#                  ip TEXT NOT NULL,
#                  timestamp DATETIME NOT NULL,
#                  user_agent TEXT,
#                  action TEXT)''')
    
#     conn.commit()
#     conn.close()

# init_db()

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

# def detect_ai_content(text):
#     """Detect AI content and properly route to quarantine when uncertain"""
#     try:
#         # Initialize the client (make sure this is done once at app startup)
#         genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
#         # Create the model instance
#         model = genai.GenerativeModel('gemini-2.5-flash')  # Updated to 1.5-flash
        
#         prompt = f"""Analyze this review text for AI-generation indicators. Consider:
# 1. Overly perfect grammar/syntax without natural errors
# 2. Generic/impersonal tone lacking specific details
# 3. Known AI phrases (like "as an AI", "language model")
# 4. Unnatural structure or formulaic praise
# 5. Disclosure statements (like "generated by ChatGPT")
# 6. Lack of personal experience details
# 7. Overuse of transition words
# 8. Uncommon word combinations

# Respond in JSON format exactly like this:
# {{
#     "judgment": "AI",  // or "HUMAN" or "QUARANTINE"
#     "confidence": 0.0-1.0,
#     "reason": "concise explanation"
# }}

# Text to analyze:
# \"\"\"{text[:2000]}\"\"\""""
        
#         response = model.generate_content(
#             prompt,
#             generation_config=GenerationConfig(
#                 temperature=0.1,
#                 max_output_tokens=300
#             )
#         )
        
#         # Parse the JSON response
#         result = json.loads(response.text)
        
#         # Map to your expected return format
#         if result['judgment'].upper() == 'AI':
#             return True, float(result['confidence']), result['reason'], 'blocked', 'auto_rejected'
#         elif result['judgment'].upper() == 'QUARANTINE':
#             return True, float(result['confidence']), result['reason'], 'quarantined', 'pending'
#         else:
#             return False, float(result['confidence']), result['reason'], 'published', 'auto_approved'
            
#     except json.JSONDecodeError:
#         print("Failed to parse Gemini response as JSON")
#         # Fallback to simple text parsing if JSON fails
#         decision = response.text.strip().upper()
#         if 'AI' in decision:
#             return True, 0.85, "AI-generated (fallback parsing)", 'blocked', 'auto_rejected'
#         elif 'HUMAN' in decision:
#             return False, 0.15, "Human-written (fallback parsing)", 'published', 'auto_approved'
#         else:
#             return True, 0.65, "Uncertain - needs review (fallback)", 'quarantined', 'pending'
            
#     except Exception as e:
#         print(f"AI Detection Error: {str(e)}")
#         # Fallback checks
#         if len(text) > 300 and len(set(text.split())) < len(text.split())/3:
#             return True, 0.7, "Possible AI (repetitive content)", 'quarantined', 'pending'
#         return False, 0.2, "Human (fallback check)", 'published', 'auto_approved'

# def detect_ai_content(text):
#     """Robust AI content detection with proper error handling"""
#     try:
#         model = genai.GenerativeModel('gemini-2.5-flash')
        
#         # Simplified but effective prompt
#         prompt = f"""Analyze this text for AI-generated content. Respond ONLY with:
# - 'AI' if definitely AI-generated
# - 'HUMAN' if definitely human-written
# - 'UNSURE' if uncertain

# Text: \"\"\"{text[:2000]}\"\"\""""
        
#         response = model.generate_content(
#             prompt,
#             generation_config=GenerationConfig(
#                 temperature=0.1,
#                 max_output_tokens=10
#             )
#         )
        
#         # Robust response parsing
#         if response.candidates and response.candidates[0].content.parts:
#             decision = response.text.strip().upper()
            
#             if decision == 'AI':
#                 return True, 0.9, "AI-generated (Gemini detection)", 'blocked', 'auto_rejected'
#             elif decision == 'UNSURE':
#                 return True, 0.6, "Potential AI content (needs review)", 'quarantined', 'pending'
        
#         # Default to human if no clear AI detection
#         return False, 0.2, "Human-written (Gemini detection)", 'published', 'auto_approved'
        
#     except Exception as e:
#         print(f"AI Detection Error: {str(e)}")
#         # Comprehensive fallback checks
#         ai_patterns = [
#             r"\bas (an )?ai\b",
#             r"\blanguage model\b",
#             r"\bgenerated (by|with)\b",
#             r"\baccording to my (knowledge|training data)\b"
#         ]
        
#         # Check for AI patterns
#         for pattern in ai_patterns:
#             if re.search(pattern, text, re.IGNORECASE):
#                 return True, 0.85, f"AI-generated (pattern: {pattern})", 'blocked', 'auto_rejected'
        
#         # Check for suspiciously perfect text
#         if len(text) > 150 and len(re.findall(r'\b\w{8,}\b', text)) > len(text.split())/3:
#             return True, 0.7, "Overly complex vocabulary", 'quarantined', 'pending'
            
#         return False, 0.3, "Human (fallback check)", 'published', 'auto_approved'

def detect_ai_content(text):
    """
    Robust AI detection using:
    1. Gemini 1.5 Pro (primary)
    2. Advanced regex patterns (fallback)
    3. Behavioral analysis (generic/unpersonalized text)
    4. Hugging Face API (secondary verification)
    """
    # Skip empty/short text (likely spam)
    if len(text.strip()) < 25:
        return False, 0.1, "Too short to analyze", 'published', 'auto_approved'

    # --- Phase 1: Gemini Detection (Primary) ---
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        prompt = f"""Analyze this text for AI-generated content. Strictly respond in JSON format:
{{
  "decision": "AI",  // "AI", "HUMAN", or "UNSURE"
  "reason": "Brief explanation",
  "confidence": 0.0-1.0
}}
Consider these indicators:
1. Overly perfect grammar/formality
2. Generic praise without personal experiences
3. Phrases like "as an AI" or "according to my knowledge"
4. Unnatural structure (e.g., excessive transitions)

Text: \"\"\"{text[:2000]}\"\"\""""

        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                temperature=0.1,
                max_output_tokens=300
            )
        )

        # Parse JSON response
        if response.text:
            try:
                result = json.loads(response.text.strip("```json\n").rstrip("```").strip())
                decision = result["decision"].upper()
                reason = result.get("reason", "AI indicators detected")
                confidence = float(result.get("confidence", 0.85))

                if decision == "AI":
                    return True, confidence, reason, 'blocked', 'auto_rejected'
                elif decision == "UNSURE":
                    return True, max(0.5, confidence), reason, 'quarantined', 'pending'
            except (json.JSONDecodeError, KeyError):
                pass  # Fall through to other checks

    except Exception as e:
        print(f"Gemini Error: {e}")

    # --- Phase 2: Regex Patterns (Fast Fallback) ---
    ai_patterns = [
        # Explicit AI disclosures
        r"\b(as|being) (an? )?(ai|language model|llm|chatbot)\b",
        r"\b(generated|created|written) (by|with|using) (ai|chatgpt|gpt|gemini|llm)\b",
        r"\baccording to (my )?(training data|knowledge base|algorithm|parameters)\b",
        
        # Generic/impersonal phrasing
        r"\b(this )?(product|item) (is )?(absolutely )?(perfect|flawless|exceptional|superb)\b",
        r"\b(highly|strongly) recommend(ed|ing)? (this|it|product)\b",
        r"\b(exceed|surpass)(ed|es)? (all|my)? expectations?\b",
        r"\b(in )?my (opinion|view|perspective|analysis)(,)? (this|it)\b",
        
        # Unnatural transitions
        r"\b(furthermore|moreover|additionally|in conclusion)\b",
        
        # Lack of personal experience
        r"\b(i (have )?(never|not) (used|tried|experienced) (this|it)\b"
    ]

    for pattern in ai_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True, 0.9, f"AI pattern: '{pattern[:30]}...'", 'blocked', 'auto_rejected'

    # --- Phase 3: Behavioral Analysis ---
    words = text.lower().split()
    word_count = len(words)
    unique_words = len(set(words))
    
    # Check for low lexical diversity
    if word_count > 80 and (unique_words / word_count) < 0.5:
        return True, 0.75, "Low lexical diversity", 'quarantined', 'pending'
        
    # Check for lack of personal pronouns
    personal_pronouns = len(re.findall(r"\b(i|me|my|mine)\b", text.lower()))
    if word_count > 50 and personal_pronouns < 2:
        return True, 0.7, "Lacks personal references", 'quarantined', 'pending'

    # --- Phase 4: Hugging Face API (Backup) ---
    if os.getenv('HF_API_KEY'):
        try:
            API_URL = "https://api-inference.huggingface.co/models/Hello-SimpleAI/chatgpt-detector-roberta"
            headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
            response = requests.post(
                API_URL, 
                headers=headers, 
                json={"inputs": text[:1000]}, 
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and data[0][0]["label"] == "AI":
                    confidence = data[0][0]["score"]
                    if confidence > 0.85:
                        return True, confidence, "AI (Hugging Face)", 'blocked', 'auto_rejected'
        except Exception as e:
            print(f"Hugging Face Error: {e}")

    # --- Final Decision ---
    return False, 0.2, "Likely human", 'published', 'auto_approved'

    
# def detect_ai_content(text):
#     """Detect AI content and properly route to quarantine when uncertain"""
#     try:
#         model = genai.GenerativeModel('gemini-2.5-flash')
        
#         prompt = f"""Analyze this text for AI-generation indicators:
# 1. Overly perfect grammar/syntax
# 2. Generic/impersonal tone
# 3. Lack of specific details
# 4. Known AI phrases

# Respond ONLY with:
# - 'AI' for definite AI content
# - 'QUARANTINE' for suspicious but uncertain
# - 'HUMAN' for definite human content

# Text: \"\"\"{text[:2000]}\"\"\""""
        
#         response = model.generate_content(
#             prompt,
#             generation_config=GenerationConfig(
#                 temperature=0.1,
#                 max_output_tokens=1
#             )
#         )
        
#         decision = response.text.strip().upper()
        
#         if decision == 'AI':
#             return True, 0.9, "Definite AI-generated content", 'blocked', 'auto_rejected'
#         elif decision == 'QUARANTINE':
#             return True, 0.65, "Suspected AI content - needs human review", 'quarantined', 'pending'
#         else:
#             return False, 0.1, "Human-written content", 'published', 'auto_approved'
            
#     except Exception as e:
#         print(f"AI Detection Error: {str(e)}")
#         # Fallback checks
#         if len(text) > 300 and len(set(text.split())) < len(text.split())/3:
#             return True, 0.7, "Possible AI (repetitive content)", 'quarantined', 'pending'
#         return False, 0.2, "Human (fallback check)", 'published', 'auto_approved'

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
    conn = get_db_connection()
    c = conn.cursor()

    # Submissions in last hour
    c.execute("""SELECT COUNT(*) AS recent_count FROM ip_activity 
                 WHERE ip = %s AND timestamp > NOW() - INTERVAL '1 hour'""", (ip,))
    count = c.fetchone()['recent_count']

    # Distinct days active
    c.execute("""SELECT COUNT(DISTINCT TO_CHAR(timestamp, 'YYYY-MM-DD')) AS active_days 
                 FROM ip_activity WHERE ip = %s""", (ip,))
    days_active = c.fetchone()['active_days'] or 1

    # Total submissions
    c.execute("""SELECT COUNT(*) AS total_submissions FROM ip_activity WHERE ip = %s""", (ip,))
    total = c.fetchone()['total_submissions']
    
    avg_per_day = total / days_active

    conn.close()

    # Thresholds
    if count > 5:
        return True, "Excessive hourly submissions"
    if avg_per_day > 3:
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
    # conn = sqlite3.connect('reviews.db')
    conn = get_db_connection()

    c = conn.cursor()
    
    # Log submission attempt
    c.execute("""INSERT INTO ip_activity 
              (ip, timestamp, user_agent, action) 
              VALUES (%s, %s, %s, %s)""",
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
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
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
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
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
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
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
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
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
                  (NULL, %s, %s, %s, %s, %s, %s)""",
                  (ip, user_agent, True, bot_conf, bot_reason, timestamp))
        c.execute("""INSERT INTO reviews 
                  (text, ip, user_agent, status, review_status, reason, confidence, timestamp, last_updated)
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
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
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
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
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""SELECT id, text, reason, confidence, timestamp 
                 FROM reviews 
                 WHERE status = 'quarantined' AND review_status = 'pending'
                 ORDER BY timestamp DESC""")
    results = c.fetchall()
    conn.close()
    return jsonify(results)


@app.route('/approve-review/<int:review_id>', methods=['POST'])
def approve_review(review_id):
    """Approve a quarantined review"""
    # conn = sqlite3.connect('reviews.db')
    conn = get_db_connection()

    c = conn.cursor()
    c.execute("""UPDATE reviews 
              SET status = 'published', 
                  review_status = 'approved',
                  last_updated = %s
              WHERE id = %s""", (datetime.now(), review_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/reject-review/<int:review_id>', methods=['POST'])
def reject_review(review_id):
    """Reject a quarantined review"""
    # conn = sqlite3.connect('reviews.db')
    conn = get_db_connection()

    c = conn.cursor()
    c.execute("""UPDATE reviews 
              SET status = 'blocked', 
                  review_status = 'rejected',
                  last_updated = %s
              WHERE id = %s""", (datetime.now(), review_id))
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
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) AS total_bots FROM bot_detections WHERE is_bot = TRUE")
    total_bots = c.fetchone()['total_bots']

    c.execute("SELECT COUNT(DISTINCT ip) AS unique_ips FROM bot_detections")
    unique_ips = c.fetchone()['unique_ips']

    c.execute("SELECT details, COUNT(*) FROM bot_detections GROUP BY details")
    detection_types = {row['details']: row['count'] for row in c.fetchall()}

    conn.close()

    return jsonify({
        'total_bots_blocked': total_bots,
        'unique_bot_ips': unique_ips,
        'detection_types': detection_types
    })

@app.route('/stats')
def stats():
    conn = get_db_connection()
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
    status_counts = c.fetchone()

    # Rejection reasons
    c.execute("""
        SELECT 
            SUM(CASE WHEN reason ILIKE '%AI%' THEN 1 ELSE 0 END) as ai_rejections,
            SUM(CASE WHEN reason ILIKE '%Paid%' THEN 1 ELSE 0 END) as paid_rejections,
            SUM(CASE WHEN reason ILIKE '%Bot%' THEN 1 ELSE 0 END) as bot_rejections,
            SUM(CASE WHEN reason ILIKE '%CAPTCHA%' THEN 1 ELSE 0 END) as captcha_rejections,
            SUM(CASE WHEN reason ILIKE '%Suspicious activity%' THEN 1 ELSE 0 END) as activity_rejections
        FROM reviews 
        WHERE status != 'published'
    """)
    rejection_reasons = c.fetchone()

    # Daily activity
    c.execute("""
        SELECT 
            TO_CHAR(timestamp, 'YYYY-MM-DD') as day,
            SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as approved,
            SUM(CASE WHEN status = 'quarantined' THEN 1 ELSE 0 END) as quarantined,
            SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked
        FROM reviews
        WHERE timestamp > NOW() - INTERVAL '7 days'
        GROUP BY day
        ORDER BY day
    """)
    daily_activity = c.fetchall()
    
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


app.secret_key = os.getenv('FLASK_SECRET_KEY')
# Frontend Routes
@app.route('/')
def home():
    return render_template('index.html')

# @app.route("/register", methods=["GET", "POST"])
# def register():
#     if request.method == "POST":
#         username = request.form.get("username")
#         password = request.form.get("password")
#         email = request.form.get("email")

#         if not (username and password and email):
#             return render_template("register.html", message="All fields are required.")

#         hashed_password = generate_password_hash(password)

#         try:
#             conn = get_db_connection()
#             cur = conn.cursor()
            
#             # Check if username or email already exists
#             cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", 
#                         (username, email))
#             existing_user = cur.fetchone()
            
#             if existing_user:
#                 return render_template("register.html", message="Username or email already exists.")
            
#             # Insert new user
#             cur.execute(
#                 "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
#                 (username, email, hashed_password)
#             )
#             user_id = cur.fetchone()['id']
#             conn.commit()
            
#             # Automatically log in the user after registration
#             session["user_id"] = user_id
#             return redirect("/dashboard")
            
#         except Exception as e:
#             conn.rollback()
#             return render_template("register.html", message="Registration failed. Please try again.")
#         finally:
#             cur.close()
#             conn.close()

#     return render_template("register.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        print(f"\n--- Registration Attempt ---")  # Debug
        print(f"Username: {username}")  # Debug
        print(f"Email: {email}")  # Debug
        print(f"Password: {password}")  # Debug

        if not (username and password and email):
            print("Missing fields!")  # Debug
            return render_template("register.html", message="All fields are required.")

        hashed_password = generate_password_hash(password)
        print(f"Hashed Password: {hashed_password}")  # Debug

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Check for existing user
            cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", 
                        (username, email))
            existing_user = cur.fetchone()
            
            if existing_user:
                print("User already exists!")  # Debug
                return render_template("register.html", 
                                    message="Username or email already exists.")
            
            # Insert new user
            try:
                print("Attempting to insert user...")  # Debug
                cur.execute(
                    "INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id",
                    (username, email, hashed_password)
                )
                user_id = cur.fetchone()['id']
                conn.commit()
                print(f"Successfully registered user ID: {user_id}")  # Debug
                
                session["user_id"] = user_id
                return redirect("/dashboard")
                
            except Exception as insert_error:
                conn.rollback()
                print(f"INSERT ERROR: {str(insert_error)}")  # Debug
                return render_template("register.html", 
                                    message=f"Registration failed. Error: {str(insert_error)}")
            
        except Exception as e:
            print(f"DATABASE ERROR: {str(e)}")  # Debug
            return render_template("register.html", 
                                message="Database error during registration.")
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

    return render_template("register.html")

# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         username = request.form.get("username")
#         password = request.form.get("password")

#         if not (username and password):
#             return render_template("login.html", message="Both username and password are required.")

#         try:
#             conn = get_db_connection()
#             cur = conn.cursor()
            
#             cur.execute("SELECT * FROM users WHERE username = %s", (username,))
#             user = cur.fetchone()
            
#             if user and check_password_hash(user['password_hash'], password):
#                 session["user_id"] = user['id']
#                 return redirect("/dashboard")
#             else:
#                 return render_template("login.html", message="Invalid username or password.")
                
#         except Exception as e:
#             return render_template("login.html", message="Login failed. Please try again.")
#         finally:
#             cur.close()
#             conn.close()

#     return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not (username and password):
            return render_template("login.html", message="Both username and password are required.")

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Changed from password_hash to password
            cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            
            # Verify against the password column
            if user and check_password_hash(user['password'], password):
                session["user_id"] = user['id']
                return redirect("/dashboard")
            else:
                return render_template("login.html", message="Invalid username or password.")
                
        except Exception as e:
            print(f"Login error: {str(e)}")  # Add debug print
            return render_template("login.html", message="Login failed. Please try again.")
        finally:
            cur.close()
            conn.close()

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT username FROM users WHERE id = %s", (session["user_id"],))
        user = cur.fetchone()
        
        if not user:
            session.clear()
            return redirect("/login")
            
        return render_template("dashboard.html", username=user['username'])
        
    except Exception as e:
        return redirect("/login")
    finally:
        cur.close()
        conn.close()

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# @app.route('/dashboard')
# def dashboard():
#     return render_template('dashboard.html')

# Add this temporary route to test connections
@app.route('/test-connections')
def test_connections():
    try:
        # Test Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Test")
        
        # Test Database
        conn = get_db_connection()
        conn.close()
        
        return jsonify({
            'gemini_status': 'working',
            'database_status': 'working'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'gemini_status': 'failed',
            'database_status': 'failed'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)