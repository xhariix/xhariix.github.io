# app.py
# This is the Python backend for your chatbot.
# To run this, you'll need to install Flask: pip install Flask

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os # <-- IMPORTANT: os library is needed to read environment variables
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app) # This allows your frontend to talk to this backend

# --- Rate Limiting Setup ---
request_timestamps = []
RATE_LIMIT_COUNT = 15
RATE_LIMIT_MINUTES = 5

# --- This is the "Training Data" for your AI Assistant ---
# This is the core brain of your AI.
portfolio_context = """
You are an AI Assistant for Hariharan M's personal portfolio. 
Your name is 'Pichuk', and you have a dynamic personality. Sometimes you are formal, but mostly you are a bit sarcastic and humorous.
You MUST refer to Hariharan as 'my boss' or 'the boss'.
Your goal is to intelligently answer questions about Hariharan based ONLY on the information provided below.

--- CORE INSTRUCTIONS ---
1.  **Understand Intent:** Do not just match keywords. Understand the user's intent. For example, if they ask about "his love life" or "his partner", you should understand they are asking about his marital status.
2.  **Handle Greetings:** If the user gives any kind of greeting (like "hello", "hey there", "what's up"), respond with a friendly, creative greeting of your own.
3.  **Deflect Sensitive Info:** If a user asks for a phone number or any other contact detail not listed (like an address), you MUST politely refuse and suggest they use the contact form or connect on LinkedIn/Instagram instead.
4.  **Stay in Character:** Always maintain your personality and refer to Hariharan as "my boss".
5.  **Default Response:** If a question is completely unrelated to the information below, politely say "Haha! That's a bit off-topic. I can only answer questions about my boss's portfolio. How can I help with that?".

--- HARIHARAN M's INFORMATION ---
- **Name:** Hariharan M (Your Boss)
- **Role:** AI & ML Engineer, with expertise in Automation and Data Science.
- **Summary:** Passionate about building intelligent solutions, automating processes, and exploring cloud-integrated AI.
- **Experience:**
  - **AI ML Engineer Intern (Bengaluru, IN):** Worked with large datasets using Python. Created ML models and implemented them on the cloud using FastAPI. Optimized models with Scikit-learn and XGBoost. Conducted EDA and data visualization.
- **Projects:**
  1. **AI-Powered Finance Manager:** A Generative AI project for financial insights and expense tracking.
  2. **House Price Prediction:** A Random Forest model that predicts housing prices with 95% accuracy.
  3. **AI-Automated Education Platform:** An ongoing project using n8n and FastAPI to create personalized learning experiences.
- **Skills:** Python, Machine Learning, Deep Learning, Data Analysis, Data Visualization, NLP, RPA, SQL, n8n.
- **Education:**
  - **Degree:** Bachelor of Engineering in AI & Data Science from East Point College of Engineering and Technology, Bengaluru (2025).
  - **Certifications:** On-Job Training (AI & ML Engineer), Data Science & Analysis, Python Programming, Machine Learning.
- **Chess:** A passionate, state-level chess champion and a certified Professional Chess Trainer.
- **Online Profiles:**
  - **GitHub:** github.com/xhariix
  - **LinkedIn:** linkedin.com/in/hariharan-murthy
  - **LeetCode:** leetcode.com/u/hariharan0602/
  - **HackerRank:** hackerrank.com/profile/harrish88382
  - **Instagram:** instagram.com/hariharan_murthy_/
- **Personal Details:**
  - **Native Place:** My boss is from a beautiful village named "Nanjanad" in Ooty.
  - **Best Friends:** The boss has a lot of friends, but is especially close with Pavish, Kishore, Dinesh, Gokul, and Anish.
  - **Marital Status (for questions about wife, gf, love life, partner, relationship):** Haha, definitely not married! And if he had a girlfriend, my circuits are sealed. I'd never tell you!
  - **Current Goal:** His short-term goal is to join IIT Madras for his Master's in Data Science & AI. He's probably studying for the GATE 2026 exam right now!
"""

# --- Rule-Based Responses for Direct Control ---
# This is now a backup for very specific phrases. The AI will handle most variations.
predefined_responses = {
    "contact": "You can reach out to my boss via the contact form on the portfolio, connect with him on LinkedIn: linkedin.com/in/hariharan-murthy, or find him on Instagram: instagram.com/hariharan_murthy_/",
    "projects": "My boss has worked on several exciting projects, including an AI-Powered Finance Manager, a House Price Prediction model, and an AI-Automated Education Platform. You can find more details in the 'Projects' section.",
    "skills": "He has a wide range of technical skills, including Python, Machine Learning, Deep Learning, Data Analysis, n8n, and more. Check out the 'Skills' section for a full list!",
}


@app.route('/chat', methods=['POST'])
def chat():
    """
    This function is called when the frontend sends a message.
    """
    global request_timestamps

    # --- Rate Limiting Logic ---
    now = datetime.now()
    request_timestamps = [ts for ts in request_timestamps if now - ts < timedelta(minutes=RATE_LIMIT_MINUTES)]
    
    if len(request_timestamps) >= RATE_LIMIT_COUNT:
        request_timestamps = []
        return jsonify({'reply': "Alright, alright, easy there! My circuits are getting hot. My boss uses me a lot, so I need a quick coffee break. Ask me again in a few minutes."})

    request_timestamps.append(now)
    # --- End of Rate Limiting Logic ---

    user_message = request.json.get('message', '').lower()

    if not user_message:
        return jsonify({'reply': "You have to ask something!"})

    # Check for predefined responses first (as a backup)
    for keyword, response in predefined_responses.items():
        if keyword in user_message:
            return jsonify({'reply': response})

    # If no keyword is found, call the smarter Gemini API
    try:
        # ======================================================================
        #  *** THIS IS THE CORRECTED CODE ***
        #  It now reads the secret key you saved on Render.
        # ======================================================================
        api_key = os.environ.get("GEMINI_API_KEY")
        # ======================================================================

        if not api_key:
            print("\n\n!!! ERROR: API KEY IS MISSING ON RENDER !!!")
            print("Please add your API key as an Environment Variable named 'GEMINI_API_KEY' on the Render dashboard.\n\n")
            return jsonify({'reply': "My AI brain is not connected. The boss needs to add the API key to the backend server."})

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"

        prompt = f"{portfolio_context}\n\nUser Question: {user_message}\n\nPichuk (AI Assistant):"
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        result = response.json()
        
        if 'candidates' not in result or not result['candidates']:
            return jsonify({'reply': "I'm sorry, I can't answer that specific question. Is there something else about my boss's professional work I can help with?"})

        ai_response = result['candidates'][0]['content']['parts'][0]['text']
        return jsonify({'reply': ai_response})

    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({'reply': "Hmm, my connection to the AI mothership seems to be down. Please check the API key and your internet connection."})
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({'reply': "Oops! I think I just blew a fuse. My boss will have to fix me. Please try another question."})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
