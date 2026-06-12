import os
import telebot
from fastapi import FastAPI, Request
from google import genai
from playwright.sync_api import sync_playwright
import uvicorn

# Tokens uthana (Hugging Face Secret se)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Hugging Face ke server ka address automatic nikalna
SPACE_ID = os.environ.get('SPACE_ID') 
WEBHOOK_URL = f"https://{SPACE_ID.replace('/', '-').lower()}.hf.space/webhook"

app = FastAPI()

@app.on_event("startup")
def on_startup():
    # Telegram ko batana ki hamara bot ab is link par active hai
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
    return {"message": "Bhai, Cloud PC Agent Webhook par ekdum मस्त chal raha hai!"}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bhai, Webhook ke sath Cloud AI Agent active ho gaya hai! Mujhe koi bhi website research ka kaam bolo.")

@bot.message_handler(func=lambda message: True)
def handle_agent_command(message):
    user_prompt = message.text
    bot.reply_to(message, "Online PC par Chrome khol raha hoon, thoda ruko...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True) 
            page = browser.new_page()
            
            ai_instruction = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"User wants to do this: '{user_prompt}'. Tell me only the exact URL they should visit first. Reply with just the URL."
            )
            target_url = ai_instruction.text.strip()
            
            if not target_url.startswith("http"):
                target_url = "https://www.google.com"

            page.goto(target_url)
            page.wait_for_timeout(4000) 
            
            screenshot_path = "pc_screen.png"
            page.screenshot(path=screenshot_path)
            browser.close()
            
        with open(screenshot_path, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption="Bhai, online PC ka screenshot yeh raha!")
            
    except Exception as e:
        bot.reply_to(message, f"Gadbad hui bhai: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
