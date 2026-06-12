import os
import telebot
from telebot import apihelper
from google import genai
from playwright.sync_api import sync_playwright

# --- PROXY SETTING (Telegram Blocking Se Bachne Ke Liye) ---
# Hum ek free public proxy use kar rahe hain taaki connection timeout na ho
apihelper.proxy = {'https': 'http://165.225.220.31:80'} 

# Hugging Face ke Secret se keys uthana
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bhai, Proxy ke sath Cloud AI Agent active ho gaya hai! Mujhe koi bhi website research ka kaam bolo.")

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
            bot.send_photo(message.chat.id, photo, caption=f"Bhai, Proxy PC par kaam ho gaya! Yeh dekho screen.")
            
    except Exception as e:
        bot.reply_to(message, f"Kuch gadbad hui bhai: {str(e)}")

if __name__ == "__main__":
    # Timeout badha kar polling chalu karna
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
    