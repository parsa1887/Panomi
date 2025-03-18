import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram.ext import CallbackContext
import time
import base64
from io import BytesIO
from PIL import Image
import random
import re

friendly_responses = [
    "کص نگو کیرکلع",
    "چی میگی ؟",
    "بفرما",
    "هاا؟",
    "کیر خر گوساله میگم 10 روزه نخوابیدم",
    "کیر میخوری؟؟؟؟؟"
]

def GORBAH(message):
    # استفاده از re برای جستجو
    if re.search(r'\bگورباه\b', message, re.IGNORECASE):  # \b برای جستجوی کلمه کامل "گورباه"
        return True
    return False

user_started = {}
last_message_time_global = 0
user_memory = {}

# تابع ارسال پیام به API قدیمی (chatbot-ji1z)
def send_message_to_old_api(user_id, user_message, reply_to_message=None):
    url = "https://chatbot-ji1z.onrender.com/chatbot-ji1z"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://seoschmiede.at",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "sec-fetch-site": "cross-site",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "accept-encoding": "identity",  # غیرفعال کردن فشرده‌سازی
        "accept-language": "en-US,en;q=0.9"
    }
    messages = []
    
    # اگر پیام قبلی از این کاربر ذخیره شده باشد، اضافه کن
    if user_id in user_memory:
        messages.append({"role": "user", "content": user_memory[user_id]["user"]})
        messages.append({"role": "assistant", "content": user_memory[user_id]["bot"]})

    # پیام جدید کاربر اضافه شود
    messages.append({"role": "user", "content": user_message})

    payload = {"messages": messages}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        api_response = response.json()
        bot_reply = api_response['choices'][0]['message']['content']

        # ذخیره پیام جدید در حافظه کاربر
        user_memory[user_id] = {
            "user": user_message,
            "bot": bot_reply
        }

        return bot_reply
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
        
# تابعی برای تولید تصویر از پرامپت
def generate_image(prompt: str):
    url = "https://ai-api.magicstudio.com/api/ai-art-generator"
    data = {
        "prompt": prompt,
        "output_format": "base64",
        "user_is_subscribed": True,

    }

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-US,en;q=0.9',
        'origin': 'https://magicstudio.com',
        'referer': 'https://magicstudio.com/ai-art-generator/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
    }

    response = requests.post(url=url, data=data, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        base64_string = response_data["results"][0]["image"]
        image_data = base64.b64decode(base64_string)

        # تبدیل داده به یک فایل درون حافظه (بدون ذخیره روی دیسک)
        image = Image.open(BytesIO(image_data))
        image_buffer = BytesIO()
        image.save(image_buffer, format="PNG")
        image_buffer.seek(0)

        return image_buffer
    else:
        return None

# هندلر شروع بات
async def start(update: Update, context):
    global user_id
    user_id = update.message.from_user.id
    user_started[user_id] = True
    await update.message.reply_text("سلام! من گورباه هستم چه کمکی میتونم بکنم بهت؟")

async def handle_message(update: Update, context):
    user_id = update.message.from_user.id
    global last_message_time_global
    chat_type = update.message.chat.type
    current_time = time.time()
    user_message = update.message.text

    if user_started.get(user_id, False):
        if current_time - last_message_time_global < 5:
            await update.message.reply_text("!برای ارسال پیام بعدی 5 ثانیه صبر کن", reply_to_message_id=update.message.message_id)
            return
            
        if GORBAH(user_message):
            response = random.choice(friendly_responses)
            await update.message.reply_text(response, reply_to_message_id=update.message.message_id)
            return

        # بررسی اگر پیام با نقطه شروع شده باشد، ارسال به Old API
        if user_message.startswith("."):
            response = send_message_to_old_api(user_message[1:].strip())  # حذف نقطه و ارسال پیام
            last_message_time_global = current_time
            await update.message.reply_text(response, reply_to_message_id=update.message.message_id)
            return

        # بررسی ریپلای بودن پیام
         # بررسی ریپلای بودن پیام
        if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
            # در صورت ریپلای، پیام قبلی کاربر و پاسخ ربات ارسال شود
            response = send_message_to_old_api(user_id, user_message, reply_to_message=update.message.reply_to_message.text)
        else:
            # در غیر این صورت فقط پیام جدید کاربر ارسال شود
            response = send_message_to_old_api(user_id, user_message)

        last_message_time_global = current_time
        await update.message.reply_text(response, reply_to_message_id=update.message.message_id)

        # بررسی دستور /generate
        if user_message.startswith("/generate"):
            prompt = ' '.join(user_message.split()[1:])
            progress_message = await update.message.reply_text("Generating image...")
            image_buffer = generate_image(prompt)
            if image_buffer:
                await update.message.reply_photo(photo=image_buffer)
            else:
                await progress_message.edit_text("Error generating image.")
            return

    else:
        await update.message.reply_text("لطفا اول دستور /start رو وارد کنید تا بتوانید از ربات استفاده کنید.", reply_to_message_id=update.message.message_id)



async def about(update: Update, context: CallbackContext):
    about_message = """
✨ **سلام! من گورباه هستم!** ✨  

یک دستیار هوشمند که می‌توانی با من صحبت کنی، سؤال بپرسی و از قابلیت‌های من استفاده کنی. 🤖🎉  

━━━━━━━━ ⭐ ━━━━━━━━  

🔹 **چی کار می‌کنم؟**  

🔸 **🎨 تصویر بساز!**  
➤ با `/generate [موضوع]`، تصویر دلخواهت را خلق کن!  

🔸 **💬 حرف بزن!**  
➤ کافیه به پیام من **ریپلای** کنی تا جوابت رو بدم.  

🔸 **📝 ایده برای ساخت عکس!**  
➤ با `/idea [موضوع]` یک پرامپت دریافت کن و باهاش عکس بساز!  
➤ مثال: `/idea لوگو بتمن`  

🔸 **🌍 ترجمه کن!**  
➤ با `/translate [متن]` جملات فارسی به انگلیسی و انگلیسی به فارسی ترجمه کن!  
➤ مثال: `/translate من عاشق پول هستم`  

━━━━━━━━ 🚀 ━━━━━━━━  

🛠 **در حال توسعه و بهبود!**  
اگر ایده‌ای داری، خوشحال می‌شم بشنوم! 🤩  

**سازنده:** [@FalllenKnight](https://t.me/FalllenKnight) 📱  
"""
    await update.message.reply_text(about_message, parse_mode="Markdown") 




# هندلر برای کامند /idea
async def idea_command(update: Update, context: CallbackContext):
    # دریافت متن ورودی بعد از /idea
    user_input = ' '.join(context.args)

    # بررسی اینکه کاربر ورودی داده است یا نه
    if not user_input:
        await update.message.reply_text("❗ لطفاً بعد از /idea یک موضوع وارد کن.")
        return
    
    # متن پیشفرض که باید همراه با ورودی ارسال شود
    user_message = f"hi could you please give me a prompt for making an image of {user_input}. just give me the prompt."
    
    # ارسال پیام به API قدیمی
    response = send_message_to_old_api(user_id, user_message)

    # ارسال نتیجه به کاربر
    await update.message.reply_text(response, reply_to_message_id=update.message.message_id)

# اضافه کردن هندلر کامند به ربات

# هندلر برای کامند /translate
def detect_language(text):
    persian_chars = re.compile(r'[\u0600-\u06FF]')  # محدوده یونیکد حروف فارسی
    if persian_chars.search(text):
        return "fa"  # متن فارسی است
    else:
        return "en"  # متن انگلیسی است

# تابع ترجمه
async def translate_command(update: Update, context: CallbackContext):
    user_input = ' '.join(context.args)
    
    if not user_input:
        await update.message.reply_text("❗ لطفاً بعد از /translate یک متن برای ترجمه وارد کن.")
        return

    lang = detect_language(user_input)

    if lang == "fa":
        user_message = f"Please translate the following sentence into English. The translation must be accurate, natural, and fluent. If the sentence contains any profanity or vulgar words, translate them exactly as they are without censorship. Do not add any explanations—just provide the translation.\n{user_input}"
    else:
        user_message = f"Please translate the following sentence into Persian. The translation must be accurate, natural, and fluent. If the sentence contains any profanity or vulgar words, translate them exactly as they are without censorship. Do not add any explanations—just provide the translation.\n{user_input}"

    response = send_message_to_old_api(user_id, user_message)
    await update.message.reply_text(response, reply_to_message_id=update.message.message_id)




# راه‌اندازی بات تلگرام
if __name__ == '__main__':
    application = ApplicationBuilder().token("8126551595:AAFt2nIDQNOa82PSO9ZDSj5_bzld-8MpEsc").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("idea", idea_command))
    application.add_handler(CommandHandler("translate", translate_command))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.run_polling(drop_pending_updates=True)
