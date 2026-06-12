import os
import telebot
from google import genai
from playwright.sync_api import sync_playwright

# Hugging Face ke Secret se keys uthana
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bhai, Cloud AI Agent Hugging Face par active hai! Mujhe koi bhi website kholne ya research ka kaam bolo.")

# Jab aap mobile telegram se koi kaam bologey
@bot.message_handler(func=lambda message: True)
def handle_agent_command(message):
    user_prompt = message.text
    bot.reply_to(message, "Online PC par Chrome khol raha hoon, thoda ruko...")

    try:
        with sync_playwright() as p:
            # Online computer ke andar bina screen wala Chrome Browser kholna
            browser = p.chromium.launch(headless=True) 
            page = browser.new_page()
            
            # AI se poochna ki is kaam ke liye kaunsi website par jana chahiye
            ai_instruction = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"User wants to do this: '{user_prompt}'. Tell me only the exact URL they should visit first. Reply with just the URL."
            )
            target_url = ai_instruction.text.strip()
            
            if not target_url.startswith("http"):
                target_url = "https://www.google.com"

            # Online computer ka browser us website par jayega
            page.goto(target_url)
            page.wait_for_timeout(4000) # 4 second rukna taaki page khul jaye
            
            # Screen ka screenshot kheenchna
            screenshot_path = "pc_screen.png"
            page.screenshot(path=screenshot_path)
            browser.close()
            
        # Screenshot aapke mobile ke telegram par bhej dena
        with open(screenshot_path, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=f"Bhai, online PC par kaam ho gaya! Yeh dekho screen.")
            
    except Exception as e:
        bot.reply_to(message, f"Kuch gadbad hui bhai: {str(e)}")

if __name__ == "__main__":
    bot.infinity_polling()
    