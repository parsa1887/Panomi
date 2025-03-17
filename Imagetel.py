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

user_memory = {}
user_started = {}
last_message_time_global = 0

# تابع ارسال پیام به API قدیمی (chatbot-ji1z)
def send_message_to_old_api(user_message):
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

     if user_id not in user_memory:
        user_memory[user_id] = []
    user_memory[user_id].append({"role": "user", "content": user_message})
    
    payload = {"messages": user_memory[user_id]}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        api_response = response.json()
        bot_reply = api_response['choices'][0]['message']['content']

        # ذخیره پاسخ ربات در حافظه
        user_memory[user_id].append({"role": "assistant", "content": bot_reply})

        # محدود کردن تعداد پیام‌های ذخیره‌شده برای هر کاربر
        if len(user_memory[user_id]) > 10:
            user_memory[user_id] = user_memory[user_id][-10:]

        return bot_reply

    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

# تابعی برای تولید تصویر از پرامپت
def generate_image(prompt: str):
    url = "https://ai-api.magicstudio.com/api/ai-art-generator"
    request_timestamp = int(time.time())

    data = {
        "prompt": prompt,
        "output_format": "base64",
        "user_profile_id": "null",
        "anonymous_user_id": "fd44c67b-0582-40cb-95b6-66cc68e24346",
        "request_timestamp": request_timestamp,
        "user_is_subscribed": False,
        "client_id": "pSgX7WgjukXCBoYwDM8G8GLnRRkvAoJlqa5eAVvj95o"
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

        # بررسی اگر پیام با نقطه شروع شده باشد، ارسال به Old API
        if user_message.startswith("."):
            response = send_message_to_old_api(user_id, user_message[1:].strip())  # حالا user_id را هم می‌فرستیم
            last_message_time_global = current_time
            await update.message.reply_text(response, reply_to_message_id=update.message.message_id)
            return

        # بررسی ریپلای بودن پیام
        if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
            response = send_message_to_old_api(user_id, user_message)
            last_message_time_global = current_time
            await update.message.reply_text(response, reply_to_message_id=update.message.message_id)
            return  

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



async def about(update: Update, context):
    about_message = """
    ✨ **سلام! من گورباه هستم!** ✨

    یک دستیار هوشمند که می‌توانی با من صحبت کنی، سؤال بپرسی و از قابلیت‌های من استفاده کنی. 🤖🎉  

    ━━━━━━━━ ⭐ ━━━━━━━━

    🔹 **چی کار می‌کنم؟**

    
    🔸 **🎨 تصویر بساز!**

    
    ➤ با `/generate [موضوع]`، تصویر دلخواهت را خلق کن!  


    🔸 **💬 حرف بزن!**

    
    ➤ کافیه به پیام من **ریپلای** کنی تا جوابت رو بدم.  

    🔸 **📝 ايده براي ساخت عکس!**

    
    ➤ ميتوني با اين دستور يک پرامپت دريافت کني و باهاش عکس بسازي!

    
    ➤ مثال : /idae لوگو بتمن

    ━━━━━━━━ 🚀 ━━━━━━━━  

    🛠 **در حال توسعه و بهبود!**
    
    اگر ایده‌ای داری، خوشحال می‌شم بشنوم! 🤩  

    **سازنده:** [@FalllenKnight](https://t.me/FalllenKnight) 📱  
    """
    await update.message.reply_text(about_message)



# هندلر برای کامند /idea
async def idea_command(update: Update, context: CallbackContext):
    # دریافت متن ورودی بعد از /idea
    user_input = ' '.join(context.args)

    # بررسی اینکه کاربر ورودی داده است یا نه
    if not user_input:
        await update.message.reply_text("❗ لطفاً بعد از /idea یک موضوع وارد کن.")
        return
    
    # متن پیشفرض که باید همراه با ورودی ارسال شود
    prompt_text = f"hi could you please give me a prompt for making an image of {user_input}. just give me the prompt."
    
    # ارسال پیام به API قدیمی
    response = send_message_to_old_api(update.message.from_user.id, prompt_text)

    # ارسال نتیجه به کاربر
    await update.message.reply_text(response, reply_to_message_id=update.message.message_id)

# اضافه کردن هندلر کامند به ربات


# راه‌اندازی بات تلگرام
if __name__ == '__main__':
    application = ApplicationBuilder().token("8126551595:AAFt2nIDQNOa82PSO9ZDSj5_bzld-8MpEsc").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("idea", idea_command))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.run_polling(drop_pending_updates=True)
