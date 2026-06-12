import os
import telebot
from fastapi import FastAPI, Request
import requests
import uvicorn

# Tokens uthana
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL')
WEBHOOK_URL = f"{RENDER_URL}/webhook"

# ⚠️ HUGGING FACE SPACE URL: Isme apne account ka sahi naam check kar lena bhai
# Agar aapka username khalid7866 hai toh: 'https://khalid7866-my-cloud-agent.hf.space/run-agent'
HF_AGENT_URL = "https://INFINITYKM-my-cloud-agent.hf.space/run-agent"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = FastAPI()

@app.on_event("startup")
def on_startup():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

@app.post("/webhook")
async def handle_webhook(request: Request):
    json_str = await request.body()
    update = telebot.types.Update.de_json(json_str.decode('utf-8'))
    bot.process_new_updates([update])
    return {"status": "ok"}

@app.get("/")
def read_root():
    return {"message": "Render Telegram Bridge Active Hai Bhai!"}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bhai, 16GB RAM wala Cloud AI Agent active ho gaya hai! Mujhe koi bhi bada task bolo.")

@bot.message_handler(func=lambda message: True)
def handle_agent_command(message):
    user_prompt = message.text
    status_msg = bot.reply_to(message, "🚀 Command mil gayi! Hugging Face ki 16GB Machine par Browser khol raha hoon, thoda ruko...")

    try:
        # Render chupke se Hugging Face ko request bhejega jahan 16GB RAM hai
        response = requests.post(HF_AGENT_URL, json={"prompt": user_prompt}, timeout=120)
        result = response.json()
        
        if result.get("status") == "success":
            summary = result.get("summary")
            bot.reply_to(message, f"✅ Kaam Poora Ho Gaya Bhai!\n\nSummary: {summary}")
        else:
            bot.reply_to(message, "Gadbad hui bhai, Hugging Face ne sahi response nahi diya.")
            
    except Exception as e:
        bot.reply_to(message, f"Bridge Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
    
