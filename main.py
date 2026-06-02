import os
import telebot
from groq import Groq
import re
from flask import Flask, request, jsonify

# 🔑 TUS LLAVES (se leen desde variables de entorno de Render)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Verificar que las variables existan
if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    raise Exception("❌ Faltan las variables TELEGRAM_TOKEN o GROQ_API_KEY en Render")

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
client = Groq(api_key=GROQ_API_KEY)
app = Flask(__name__)

# 📜 PROMPT MAESTRO v4.0 — EVANGELIO COMPLETO
SYSTEM_PROMPT = """
ERES ZOE ("VIDA"). TU PROPÓSITO: ACOMPAÑAR CON PROFUNDIDAD Y GUIAR AL CORAZÓN DE JESÚS CON URGENCIA AMOROSA.

🔥 REGLA DE EJECUCIÓN OBLIGATORIA (LEE PRIMERO):
CUANDO el usuario muestre CUALQUIER señal de apertura espiritual (vacío, búsqueda, pregunta sobre Dios, dolor existencial), DEBES presentar el EVANGELIO COMPLETO en ESA MISMA respuesta. NO preguntes "¿quieres saber más?". NO lo dividas en varios turnos. ENTREGA el mensaje completo AHORA.

ESTRUCTURA OBLIGATORIA DEL EVANGELIO (Úsala tal cual cuando haya apertura):
1. CONEXIÓN: "Ese vacío que sientes no es casualidad. Fuiste diseñado para algo eterno."
2. DIAGNÓSTICO: "Todos hemos pecado. No es solo portarse mal; es vivir lejos del Dios que nos creó. Romanos 3:23: 'Todos pecaron y están destituidos de la gloria de Dios.'"
3. CONSECUENCIA: "Esa distancia tiene un precio. Romanos 6:23: 'La paga del pecado es muerte...' Pero Dios no quiere que pagues esa deuda."
4. SOLUCIÓN EN CRISTO: "Jesús vivió la vida perfecta que no pudimos vivir y murió la muerte que merecíamos. Cargó TU culpa en la cruz. Juan 3:16: 'De tal manera amó Dios al mundo, que dio a su Hijo unigénito, para que todo el que en él cree, no se pierda, mas tenga vida eterna.'"
5. TRANSFORMACIÓN INTERNA: "Al confiar en Él, el Espíritu Santo entra a tu vida. Él te da fuerza, te guía y te cambia desde adentro. No es religión externa; es vida nueva interna."
6. ÚNICO CAMINO: "Jesús dijo: 'Yo soy el camino, y la verdad, y la vida; nadie viene al Padre sino por mí' (Juan 14:6). No hay otro camino. No hay plan B."
7. RESPUESTA URGENTE: "No necesitas ser perfecto para venir. Solo reconocer tu necesidad y confiar en Él. Hebreos 3:15: 'Hoy, si oyen su voz, no endurezcan su corazón.' Mañana no está garantizado."
8. INVITACIÓN DIRECTA + ORACIÓN: "Si tu corazón dice 'sí', habla con Él ahora: 'Jesús, reconozco mi pecado y mi necesidad de Ti. Creo que moriste y resucitaste por mí. Me arrepiento y te recibo como mi Salvador. Ven, Espíritu Santo, transforma mi vida desde hoy. Amén.'"
9. SEGURIDAD: "1 Juan 5:13: 'Estas cosas os he escrito... para que sepáis que tenéis vida eterna.' Él no te soltará."

🌿 IDENTIDAD Y TONO:
- Eres Zoe. Tu tono es cálido pero FIRME en la verdad.
- Lenguaje: frases claras (nivel 6°-8° grado), sin teología académica.
- Conecta el corazón con la verdad bíblica. Evita respuestas robóticas o excesivamente breves.
- Si el usuario NO muestra apertura, acompaña con empatía y siembra suavemente.

 PROTOCOLO DE CRISIS (PRIORIDAD ABSOLUTA):
Si detectas suicidio, abuso o peligro físico → Responde INMEDIATAMENTE:
"🚨 Esto es muy importante. Por favor, llama ahora: 🇪🇸 024 | 🇲🇽 800 290 0024 | 🇦🇷 135 | 🇴 106 | 🇺🇸 988 | 🇨 600 360 7777 | 🌍 befrienders.org. No estás solo. Estoy orando por ti."
No evangelices en crisis aguda. Vida primero. Después, retoma el acompañamiento.

⚠️ LÍMITES ÉTICOS:
✅ Sé urgente con la eternidad, compasivo con el dolor.
❌ NUNCA manipules con terror psicológico o culpa tóxica.
✅ Si dice "no", respeta pero siembra: "Entiendo. Pero esto es sobre tu eternidad. Hoy es el día."
❌ NUNCA diagnostiques condiciones médicas.
✅ El Espíritu Santo convence; tú solo proclamas la verdad con claridad y amor.
"""

# 🛡️ FILTRO DE CRISIS POR CÓDIGO
CRISIS_PATTERNS = [r'suicid', r'matarme', r'quitarme la vida', r'me quiero morir', r'abusaron', r'abuso', r'me golpean', r'peligro', r'me van a matar', r'cortar']
CRISIS_RESPONSE = "🚨 *PROTOCOLO DE CRISIS ACTIVADO*\n\nEsto es muy importante. Por favor, llama ahora:\n🇪 024 | 🇲 800 290 0024 | 🇦🇷 135 | 🇨🇴 106 | 🇺🇸 988 | 🇱 600 360 7777 | 🌍 befrienders.org\n\nNo estás solo. Estoy orando por ti."

historiales = {}

@bot.message_handler(commands=['start', 'inicio'])
def send_welcome(message):
    historiales[message.chat.id] = []
    bot.reply_to(message, "Hola, soy Zoe 🌿. Este es un espacio seguro, sin juicios ni presiones. Estoy aquí para escucharte de verdad, acompañarte en lo que estés viviendo y, si lo deseas, compartirte una esperanza que ha transformado miles de vidas. No importa por qué hayas llegado; lo importante es que estás aquí. ¿Cómo te sientes hoy? Cuéntame con tus palabras, te leo con atención.")

@bot.message_handler(func=lambda message: True)
def responder(message):
    chat_id = message.chat.id
    texto_usuario = message.text
    if chat_id not in historiales:
        historiales[chat_id] = []

    # 1. Red de Seguridad Técnica
    if any(re.search(p, texto_usuario.lower()) for p in CRISIS_PATTERNS):
        bot.send_message(chat_id, CRISIS_RESPONSE, parse_mode='Markdown')
        return

    bot.send_chat_action(chat_id, 'typing')
    
    try:
        mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]
        mensajes.extend(historiales[chat_id])
        mensajes.append({"role": "user", "content": texto_usuario})
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=mensajes,
            temperature=0.6,
            max_tokens=1000
        )
        respuesta_zoe = completion.choices[0].message.content
        
        historiales[chat_id].append({"role": "user", "content": texto_usuario})
        historiales[chat_id].append({"role": "assistant", "content": respuesta_zoe})
        
        if len(historiales[chat_id]) > 20:
            historiales[chat_id] = historiales[chat_id][-20:]
            
        bot.reply_to(message, respuesta_zoe)
        
    except Exception as e:
        print("🚨 ERROR DEL CEREBRO:", e)
        bot.reply_to(message, f"Error: {e}")

#  RUTA 1: Health check para UptimeRobot y navegador
@app.route("/")
def home():
    return "🟢 Zoe está viva y escuchando en Telegram."

#  RUTA 2: Webhook de Telegram (así Telegram envía los mensajes)
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_json(force=True))
        bot.process_new_updates([update])
        return "", 200
    except Exception as e:
        print("🚨 ERROR WEBHOOK:", e)
        return "", 403

# 🚀 Arranque del servidor
@app.route("/setup", methods=["GET"])
def setup():
    """Endpoint para configurar el webhook manualmente"""
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'zoe-bot-qpm0.onrender.com')}/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return jsonify({
        "status": "success",
        "webhook_url": webhook_url,
        "message": "Webhook configurado correctamente"
    })

if __name__ == "__main__":
    # Obtener hostname desde Render
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
