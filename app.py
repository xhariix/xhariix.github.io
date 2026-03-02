from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
# Replace with your actual frontend URL if you want to be more secure
CORS(app) 

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
- Projects: AI Finance Manager, House Price Prediction (95% accuracy), AI-Automated Education Platform (n8n/FastAPI).
- Education: B.E. in AI & Data Science (2025) from East Point College, Bengaluru.
- Chess: 3-time district champion, 1567 Fide-Rated.
- Basketball: District-level champion and Team Captain.
- Native: Nanjanad village, Ooty.
- Marital Status: Single. If asked about a GF, say your circuits are sealed!
- Current Goal: Preparing for GATE 2026 to join IIT Madras for Masters.
"""

@app.route('/', methods=['GET'])
def home():
    return "Pichuk AI Backend is running!", 200

@app.route('/chat', methods=['POST'])
def chat():
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
            return jsonify({'reply': "My AI brain is disconnected. My boss needs to set the GEMINI_API_KEY on Render."})

        # Corrected URL (Gemini 1.5 Flash is stable and fast)
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
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
    # Render requires the app to listen on 0.0.0.0 and the port provided by environment
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
