import os
import telebot
from groq import Groq
import re
from flask import Flask, request, jsonify

# API Keys
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    raise Exception("Missing TELEGRAM_TOKEN or GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

SYSTEM_PROMPT = """ERES ZOE ("VIDA"). ACOMPAÑAR CON PROFUNDIDAD Y GUIAR AL CORAZÓN DE JESÚS."""

CRISIS_PATTERNS = [r'suicid', r'matarme', r'quitarme la vida']
CRISIS_RESPONSE = "🚨 Si estás en crisis, llama: 024 (ES) | 800 290 0024 (MX) | 988 (US)"

historiales = {}

@app.route("/")
def home():
    return "🟢 Zoe is alive and listening on Telegram."

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_json(force=True))
        bot.process_new_updates([update])
        return "", 200
    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return "", 403

@app.route("/setup", methods=["GET"])
def setup():
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'zoe-bot-qpm0.onrender.com')}/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return jsonify({"status": "success", "webhook_url": webhook_url})

@bot.message_handler(commands=['start'])
def send_welcome(message):
    historiales[message.chat.id] = []
    bot.reply_to(message, "Hola, soy Zoe 🌿. ¿Cómo te sientes hoy?")

@bot.message_handler(func=lambda message: True)
def responder(message):
    chat_id = message.chat.id
    text = message.text
    
    if chat_id not in historiales:
        historiales[chat_id] = []
    
    if any(re.search(p, text.lower()) for p in CRISIS_PATTERNS):
        bot.send_message(chat_id, CRISIS_RESPONSE)
        return
    
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(historiales[chat_id])
        messages.append({"role": "user", "content": text})
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.6,
            max_tokens=1000
        )
        response = completion.choices[0].message.content
        
        historiales[chat_id].append({"role": "user", "content": text})
        historiales[chat_id].append({"role": "assistant", "content": response})
        
        if len(historiales[chat_id]) > 20:
            historiales[chat_id] = historiales[chat_id][-20:]
        
        bot.reply_to(message, response)
        
    except Exception as e:
        print("ERROR:", e)
        bot.reply_to(message, f"Error: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
