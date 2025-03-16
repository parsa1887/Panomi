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
    payload = {"messages": [{"role": "user", "content": user_message}]}
    proxies = {"http": None, "https": None}
    try:
        response = requests.post(url, json=payload, headers=headers, proxies=proxies)
        response.raise_for_status()
        api_response = response.json()
        return api_response['choices'][0]['message']['content']
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
    current_time = time.time()

    if user_started.get(user_id, False):
        if current_time - last_message_time_global < 5:
            await update.message.reply_text("!برای ارسال پیام بعدی 5 ثانیه صبر کن", reply_to_message_id=update.message.message_id)
            return

        
        user_message = update.message.text
        print(f"User: {user_message}")

        # بررسی اگر پیام شامل کامند /t باشد
        if user_message.startswith("/t"):
            # حذف /t از ابتدا و ارسال پیام به API قدیمی
            response = send_message_to_old_api(user_message[2:].strip())  # حذف فضای اضافی
            print(f"ChatBot: {response}")
            last_message_time_global = current_time
            await update.message.reply_text(response, reply_to_message_id=update.message.message_id)
        # بررسی اگر پیام شامل دستور تولید تصویر باشد
        elif user_message.startswith("/generate"):
            prompt = ' '.join(user_message.split()[1:])
            progress_message = await update.message.reply_text("Generating image...")
            image_buffer = generate_image(prompt)
            if image_buffer:
                await update.message.reply_photo(photo=image_buffer)
            else:
                await progress_message.edit_text("Error generating image.")
    else:
        await update.message.reply_text("لطفا اول دستور /start رو وارد کنید تا بتوانید از ربات استفاده کنید.", reply_to_message_id=update.message.message_id)



async def about(update: Update, context):
    about_message = """
    🌟 **سلام! من گورباه هستم!** 🌟

    من یک مدل زبانی هوشمندم که می‌توانی با من صحبت کنی، سوالاتت را بپرسی و از امکانات جالب من استفاده کنی. 😊  

    👨‍💻 **ویژگی‌های من:**  
    - با دستور `/generate` می‌توانی تصاویر دلخواهت را بسازی. کافیست موضوع را مشخص کنی و من یک تصویر جادویی برایت خلق می‌کنم! 🎨  
    - می‌توانم محاسبات ریاضی را برایت انجام دهم، فقط کافیست مسئله‌ی خود را ارسال کنی.  
      - **مثال:** `22+70`  

    📝 **چطور با من صحبت کنی؟**  
    - برای ارسال پیام، کافیست قبل از متن دو اسلش (`/t`) قرار دهی.  
      - **مثال:** `/tسلام گورباه!`  

    🔧 **نکات مهم:**  
    - من در حال یادگیری و بهبود هستم تا بتوانم بهتر کمکت کنم. اگر پیشنهادی داری، خوشحال می‌شوم بشنوم! 🤖  

    **سازنده:** [@FalllenKnight](https://t.me/FalllenKnight) 📱  
    """
    # در اینجا از MarkdownV2 برای فرار دادن کاراکترهای خاص استفاده می‌شود.
    await update.message.reply_text(about_message)


async def handle_math(update: Update, context: CallbackContext):
    user_message = update.message.text.strip()

    # الگوی جستجو برای عملیات ریاضی (جمع، تفریق، ضرب، تقسیم)
    pattern = r'(\d+)\s*([+\-*/])\s*(\d+)'

    match = re.search(pattern, user_message)

    if match:
        num1 = int(match.group(1))
        operator = match.group(2)
        num2 = int(match.group(3))

        # محاسبه جواب
        if operator == '+':
            result = num1 + num2
        elif operator == '-':
            result = num1 - num2
        elif operator == '*':
            result = num1 * num2
        elif operator == '/':
            if num2 != 0:
                result = num1 / num2
            else:
                result = "خطا! تقسیم بر صفر مجاز نیست."

        # ارسال نتیجه به کاربر
        await update.message.reply_text(f"نتیجه {user_message} برابر با {result}")

# هندلر برای شناسایی پیام‌های ریاضی و ارسال نتیجه
math_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_math)

# راه‌اندازی بات تلگرام
if __name__ == '__main__':
    application = ApplicationBuilder().token("8126551595:AAFt2nIDQNOa82PSO9ZDSj5_bzld-8MpEsc").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(math_handler)
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.run_polling(drop_pending_updates=True)
