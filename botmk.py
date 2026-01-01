Import logging
import requests
import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- वेब सर्वर (बोट को 24/7 जगाए रखने के लिए) ---
app = Flask('')

@app.route('/')
def home():
    return "बोट ऑनलाइन है! 🚀"

def run_web():
    # Render और अन्य प्लेटफार्म्स के लिए पोर्ट 8080 का उपयोग
    app.run(host='0.0.0.0', port=8080)

# --- आपकी सीक्रेट डिटेल्स ---
BOT_TOKEN = "8552608622:AAFk40ouSuoK-AbQl2r8qjszgCLnTU6BRbM"
REMOVE_BG_API_KEY = "fBJrBEt8XaUH8WY5wqXiW58y"

# लॉगिंग सेटअप (ताकि एरर का पता चल सके)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"नमस्ते {user_name}! 👋\nमुझे कोई भी फोटो भेजें, मैं उसका बैकग्राउंड तुरंत हटा दूँगा।")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # प्रोसेसिंग मैसेज दिखाएँ
        status_msg = await update.message.reply_text("फोटो प्रोसेस हो रही है... कृपया रुकें ⏳")
        
        # टेलीग्राम से फोटो फाइल डाउनलोड करें
        photo_file = await update.message.photo[-1].get_file()
        input_path = "input_image.jpg"
        await photo_file.download_to_drive(input_path)

        # Remove.bg API को कॉल करें
        with open(input_path, 'rb') as img_file:
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': img_file},
                data={'size': 'auto'},
                headers={'X-Api-Key': REMOVE_BG_API_KEY},
            )

        # अगर सफलता मिली (Status 200)
        if response.status_code == 200:
            output_path = "no_bg.png"
            with open(output_path, 'wb') as out:
                out.write(response.content)
            
            # बिना बैकग्राउंड वाली फाइल भेजें
            await update.message.reply_document(
                document=open(output_path, 'rb'), 
                filename='background_removed.png',
                caption="लीजिए! आपकी फोटो तैयार है। ✅"
            )
            await status_msg.delete()
        else:
            # API से मिलने वाला एरर मैसेज
            error_data = response.json()
            error_msg = error_data.get('errors', [{}])[0].get('title', 'Unknown Error')
            await update.message.reply_text(f"❌ एरर: {error_msg}\n(शायद आपकी API लिमिट खत्म हो गई है)")

        # अस्थायी फाइलें डिलीट करें
        if os.path.exists(input_path): os.remove(input_path)
        if 'output_path' in locals() and os.path.exists(output_path): os.remove(output_path)

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("⚠️ कुछ तकनीकी दिक्कत आ गई। कृपया बाद में प्रयास करें।")

def main():
    # वेब सर्वर को बैकग्राउंड थ्रेड में शुरू करें
    threading.Thread(target=run_web, daemon=True).start()

    # टेलीग्राम बोट शुरू करें
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("बोट और वेब सर्वर सफलतापूर्वक चालू हो गए हैं!")
    application.run_polling()

if __name__ == '__main__':
    main()