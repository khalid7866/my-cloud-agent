import os
import telebot
from fastapi import FastAPI, Request
from google import genai
from google.genai import types
from playwright.sync_api import sync_playwright
import uvicorn

# Tokens uthana
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL')
WEBHOOK_URL = f"{RENDER_URL}/webhook"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

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
    return {"message": "Agent dynamic mode me chal raha hai!"}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bhai, Asali Cloud PC Agent active ho gaya hai! Mujhe koi bada kaam bolo (Jaise: 'Google par jaakar taj mahal search karo aur pehli website kholo')")

@bot.message_handler(func=lambda message: True)
def handle_agent_command(message):
    user_prompt = message.text
    status_msg = bot.reply_to(message, "Agent ne dimaag chalana shuru kiya... Browser khol raha hoon.")

    try:
        with sync_playwright() as p:
            # Browser open karna
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 720})
            
            # Shuruat me Google par jana
            page.goto("https://www.google.com")
            
            step = 1
            max_steps = 5  # AI maximum 5 baar khud se koshish karega kaam poora karne ki
            
            while step <= max_steps:
                screenshot_path = f"step_{step}.png"
                page.screenshot(path=screenshot_path)
                
                # Gemini AI ko screenshot aur user ki command bhejna taaki woh agla kadam soche
                with open(screenshot_path, "rb") as f:
                    image_bytes = f.read()
                
                system_instruction = (
                    "You are a Cloud PC Agent. Look at the screenshot of the browser and the user's ultimate goal. "
                    "Decide the next single action to take to achieve the goal. "
                    "Your response must be in one of these exact formats:\n"
                    "GOTO: <url>\n"
                    "CLICK: <text or selector>\n"
                    "TYPE: <text> INTO <selector>\n"
                    "DONE: <final answer summary>\n"
                    "If the goal is achieved, reply with DONE."
                )
                
                response = ai_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type='image/png'),
                        f"User Goal: {user_prompt}\nWhat should be the next single action based on this current screenshot?"
                    ],
                    config=types.GenerateContentConfig(system_instruction=system_instruction)
                )
                
                ai_action = response.text.strip()
                bot.edit_message_text(f"Step {step}: AI ne faisla liya -> {ai_action}", message.chat.id, status_msg.message_id)
                
                # AI ke faisle ke mutabik kaam karna
                if ai_action.startswith("GOTO:"):
                    url = ai_action.replace("GOTO:", "").strip()
                    page.goto(url)
                elif ai_action.startswith("CLICK:"):
                    target = ai_action.replace("CLICK:", "").strip()
                    # Selector ya text par click karne ki koshish
                    try:
                        page.click(f"text={target}", timeout=3000)
                    except:
                        page.click(target, timeout=3000)
                elif ai_action.startswith("TYPE:"):
                    parts = ai_action.replace("TYPE:", "").split("INTO")
                    text_to_type = parts[0].strip()
                    selector = parts[1].strip()
                    page.fill(selector, text_to_type)
                    page.keyboard.press("Enter")
                elif ai_action.startswith("DONE:"):
                    # Kaam poora ho gaya! Final screenshot bhejo
                    with open(screenshot_path, "rb") as photo:
                        bot.send_photo(message.chat.id, photo, caption=f"Bhai, kaam poora ho gaya!\nSummary: {ai_action.replace('DONE:', '').strip()}")
                    break
                
                page.wait_for_timeout(3000)
                step += 1
                
            browser.close()
            
    except Exception as e:
        bot.reply_to(message, f"Agent fail ho gaya bhai: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
    
