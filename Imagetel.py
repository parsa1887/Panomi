import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram.ext import CallbackContext
import time
import base64
from io import BytesIO
from PIL import Image
import random

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

# هندلر برای دریافت پیام‌ها و ارسال آن به API
# هندلر برای دریافت پیام‌ها و ارسال آن به API
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

        # بررسی اگر پیام شامل دو اسلش باشد
        if user_message.startswith("//"):
            # برش دادن دو اسلش از ابتدا و ارسال پیام به API قدیمی
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

    یک مدل زبانی که می‌توانی با من صحبت کنی، سوالات خودت رو بپرسی، و با امکانات جالب من آشنا بشی. 😊

    👨‍💻 **امکانات من:**
    - با استفاده از دستور `/generate` می‌تونی عکس‌های دلخواهت رو بسازی. فقط کافیه موضوع رو به من بدی و من برات یک تصویر جادویی خلق می‌کنم! 🎨

    🎮 **بازی‌ها:**
    - دستور `/game` رو وارد کن تا با من یه بازی ریاضی سرگرم‌کننده بازی کنی! 🧠

    📝 **چطور با من صحبت کنی؟**
    - برای صحبت با من، فقط کافیه پیام خودت رو بنویسی و قبلش دو تا اسلش (`//`) بزاری. مثلاً: `//سلام گورباه!`

    🔧 **توضیحات:**
    - من در حال یادگیری هستم تا بتونم بهتر با شما ارتباط برقرار کنم. به من بگو که چطور می‌توانم کمک کنم! 🤖

    **Creator:** [@FalllenKnight](https://t.me/FalllenKnight) 📱
    """
    await update.message.reply_text(about_message, parse_mode="MarkdownV2")


user_game_status = {}

# تابعی برای شروع بازی ریاضی
async def start_game(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    # بررسی اینکه آیا کاربر در حال بازی است
    if user_id in user_game_status and user_game_status[user_id]:
        await update.message.reply_text("شما در حال حاضر در بازی هستید. برای خروج دوباره دستور /game را وارد کنید.")
        return

    # شروع بازی
    user_game_status[user_id] = True
    await update.message.reply_text("بازی ریاضی شروع شد! من یک سوال از شما می‌پرسم، شما باید جواب صحیح رو ارسال کنید.")

    # تولید یک سوال ریاضی تصادفی
    operator = random.choice(['+', '-', '*', '/'])
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)

    if operator == '/':
        # اگر عملیات تقسیم باشد، اطمینان حاصل می‌کنیم که تقسیم بر صفر نشود و جواب صحیح به دست بیاید.
        num1 = num1 * num2

    question = f"چه می‌شود اگر {num1} {operator} {num2}؟"
    answer = eval(f"{num1} {operator} {num2}")

    # ذخیره جواب درست برای مقایسه بعدی
    user_game_status[user_id] = (answer, question)
    await update.message.reply_text(question)

# تابعی برای بررسی جواب کاربر
async def check_answer(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_game_status or not user_game_status[user_id]:
        return  # اگر کاربر در حال بازی نباشد، جواب را بررسی نمی‌کنیم

    correct_answer, question = user_game_status[user_id]

    if update.message.text.strip() == str(correct_answer):
        await update.message.reply_text(f"درست است! پاسخ شما صحیح است.\nبرای شروع بازی جدید /game را وارد کنید.")
        user_game_status[user_id] = False  # بازی به پایان می‌رسد
    else:
        await update.message.reply_text(f"پاسخ اشتباه است! دوباره تلاش کنید.\nسوال: {question}")

# تابعی برای خروج از بازی
async def end_game(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_game_status and user_game_status[user_id]:
        user_game_status[user_id] = False
        await update.message.reply_text("بازی تمام شد. می‌توانید از دستورهای دیگر استفاده کنید.")
    else:
        await update.message.reply_text("شما در حال حاضر در بازی نیستید.")

# هندلر برای شروع بازی و بررسی جواب‌ها
async def handle_game(update: Update, context: CallbackContext):
    user_message = update.message.text.strip().lower()

    if user_message == '/game':
        await start_game(update, context)
    elif user_message.isdigit():
        await check_answer(update, context)

# راه‌اندازی بات تلگرام
if __name__ == '__main__':
    application = ApplicationBuilder().token("8126551595:AAFt2nIDQNOa82PSO9ZDSj5_bzld-8MpEsc").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("game", start_game))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.run_polling(drop_pending_updates=True)
