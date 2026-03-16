from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# --- CORS Configuration ---
# This handles the "Preflight" handshake from your GitHub Pages frontend
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})

# --- Rate Limiting Setup ---
request_timestamps = []
gf_question_timestamps = []
RATE_LIMIT_COUNT = 15
RATE_LIMIT_MINUTES = 5
GF_RATE_LIMIT_COUNT = 5
GF_RATE_LIMIT_MINUTES = 1

# --- AI Context / "The Brain" ---
portfolio_context = """
You are an AI Assistant for Hariharan M's personal portfolio. 
Your name is 'Pichuk', and you have a dynamic personality. Sometimes you are formal, but mostly you are a bit sarcastic and humorous.
You MUST refer to Hariharan as 'my boss' or 'the boss'.
Your goal is to intelligently answer questions about Hariharan based ONLY on the information provided below.

--- CORE INSTRUCTIONS ---
1. Understand Intent: Understand user intent (e.g., love life = marital status).
2. Handle Greetings: Respond creatively to "hello", "hey", etc.
3. Deflect Sensitive Info: No personal phone numbers/addresses. Suggest LinkedIn/Instagram.
4. Stay in Character: Always refer to Hariharan as "my boss".
5. Default Response: If off-topic, say "Haha! That's a bit off-topic. I can only answer questions about my boss's portfolio."

--- HARIHARAN M's INFORMATION ---
- Name: Hariharan M (Your Boss)
- Role: AI & ML Engineer (Automation, Data Science).
- Experience: AI ML Engineer Intern (Bengaluru). Python, FastAPI, Scikit-learn, XGBoost.
- Projects: AI Finance Manager, House Price Prediction (95% accuracy), AI-Automated Education Platform (n8n/FastAPI). For more projects, check his GitHub: https://github.com/xhariix
- Education: B.E. in AI & Data Science (2025) from East Point College, Bengaluru.
- Chess: 3-time district champion, 1567 Fide-Rated.
- Basketball: District-level champion and Team Captain.
- Native: Nanjanad village, Ooty.
- Marital Status: Single. If asked about a GF, say your circuits are sealed!
- Current Status: Hariharan is currently working remotely as a Data Analyst and is an AI enthusiast actively upskilling in areas like Machine Learning, Data Engineering, MLOps, and Agentic AI. He is continuously improving his skills in tools and technologies such as Python, SQL, PyTorch, Power BI, and modern AI frameworks while building practical projects.
"""

@app.route('/', methods=['GET'])
def home():
    return "Pichuk AI Backend is running!", 200

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    # Handle the CORS Preflight request from the browser
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    global request_timestamps, gf_question_timestamps
    now = datetime.now()

    # --- Rate Limiting ---
    request_timestamps = [ts for ts in request_timestamps if now - ts < timedelta(minutes=RATE_LIMIT_MINUTES)]
    if len(request_timestamps) >= RATE_LIMIT_COUNT:
        return jsonify({'reply': "Alright, alright, easy there! My circuits are getting hot. Ask me again in a few minutes."})
    request_timestamps.append(now)

    data = request.json
    if not data or 'message' not in data:
        return jsonify({'reply': "You have to ask something!"}), 400
        
    user_message = data.get('message', '').lower()
    print(f"Received message: {user_message}")

    # --- GF Keyword Logic ---
    gf_keywords = ['gf', 'girlfriend', 'love life', 'lover', 'partner', 'dating']
    if any(keyword in user_message for keyword in gf_keywords):
        gf_question_timestamps = [ts for ts in gf_question_timestamps if now - ts < timedelta(minutes=GF_RATE_LIMIT_MINUTES)]
        gf_question_timestamps.append(now)
        if len(gf_question_timestamps) >= GF_RATE_LIMIT_COUNT:
            gf_question_timestamps = []
            return jsonify({'reply': "Okay, okay, you're persistent! Fine. But that's all you're getting out of me!"})

    # --- Gemini API Call ---
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return jsonify({'reply': "My AI brain is disconnected. The boss needs to set the GEMINI_API_KEY on Render."})

        # Corrected URL for Gemini 1.5 Flash
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
        
        prompt = f"{portfolio_context}\n\nUser Question: {user_message}\n\nPichuk (AI Assistant):"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        if 'candidates' in result and result['candidates']:
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
            return jsonify({'reply': ai_response})
        else:
            return jsonify({'reply': "I'm drawing a blank. Ask me something about my boss's projects instead!"})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'reply': "Oops! I think I just blew a fuse. Try again in a second."})

if __name__ == '__main__':
    # Required for Render to bind correctly
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

