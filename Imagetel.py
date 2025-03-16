import requests
import base64
from io import BytesIO
from PIL import Image
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# توکن ربات تلگرام خود را اینجا قرار بده
TELEGRAM_API_TOKEN = ''

# URL API برای تولید تصویر
url = "https://ai-api.magicstudio.com/api/ai-art-generator"

# تابعی برای تولید تصویر از پرامپت
def generate_image(prompt: str):
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

# تابع برای دستور /generate
async def generate(update: Update, context: CallbackContext):
    if context.args:
        prompt = ' '.join(context.args)
        progress_message = await update.message.reply_text("Generating...")

        try:
            image_buffer = generate_image(prompt)
            if image_buffer:
                await update.message.reply_photo(photo=image_buffer)
            else:
                await progress_message.edit_text("Error generating image.")
        except Exception as e:
            await progress_message.edit_text(f"An error occurred: {str(e)}")
    else:
        await update.message.reply_text("Please provide a prompt after /generate.")

# تابع اصلی برای راه‌اندازی ربات
def main():
    application = Application.builder().token(TELEGRAM_API_TOKEN).build()
    application.add_handler(CommandHandler("generate", generate))
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
