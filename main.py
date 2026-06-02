from flask import Flask, request
import os
import telebot
from groq import Groq

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

SYSTEM_PROMPT = """Eres Zoe. Acompañas y guías al corazón de Jesús con urgencia amorosa."""

@app.route("/")
def hello():
    return "Zoe is working!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_json(force=True))
        bot.process_new_updates([update])
        return "", 200
    except:
        return "", 403

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hola, soy Zoe 🌿. ¿Cómo te sientes hoy?")

@bot.message_handler(func=lambda message: True)
def responder(message):
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.append({"role": "user", "content": message.text})
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.6,
            max_tokens=1000
        )
        response = completion.choices[0].message.content
        
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
