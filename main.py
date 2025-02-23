import os
import time
import requests
import zstandard as zstd
import json
from PIL import Image
from io import BytesIO
from flask import Flask, request
from pyrogram import Client, filters
from pyrogram.types import Message

# Initialize Flask app
app = Flask(__name__)

# Telegram Bot API
API_ID = "7405235"
API_HASH = "5c9541eefe8452186e9649e2effc1f3f"
BOT_TOKEN = "6627182185:AAEBRayb9vuLUbjbmwd-NwP0fssteLsDcgU"

# Initialize Pyrogram Client
bot = Client("photo-enhancer-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.route("/")
def home():
    return "Bot is running on Vercel!"

@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    """Handle incoming updates from Telegram"""
    update = request.get_json()
    bot.process_update(update)
    return "ok", 200

@bot.on_message(filters.command(["enhance", "upscale", "ups"]))
async def upscale_command(client: Client, message: Message):
    """Handle image enhancement"""
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply_text("❗ Reply to an image with /upscale to process it.")

    processing_msg = await message.reply_text("🔄 Processing image...")
    image_path = None

    try:
        # Download the image
        image_path = await message.reply_to_message.download()

        # Upload the image and get the processing code
        code = upload_image(image_path)
        if not code:
            raise RuntimeError("Image upload failed")

        # Get processed image URL
        img_url = f"https://photoai.imglarger.com/restore/{code}.jpg"

        # Send the processed image
        await processing_msg.delete()
        await message.reply_photo(img_url, caption="✨ Enhanced image ready!")

    except Exception as e:
        await processing_msg.edit_text(f"❌ Error: {str(e)}")
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

def upload_image(image_path: str) -> str:
    """Upload image to the processing API"""
    url = "https://photoai.imglarger.com/api/PhoAi/Upload"

    with open(image_path, 'rb') as image_file:
        files = {
            'file': (os.path.basename(image_path), image_file, 'image/jpeg')
        }
        data = {'type': 8}
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }

        response = requests.post(url, headers=headers, data=data, files=files)
        response.raise_for_status()

        json_response = response.json()
        if json_response.get("msg") == "Success":
            return json_response["data"]["code"]
        else:
            raise Exception(json_response)

# Start Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
