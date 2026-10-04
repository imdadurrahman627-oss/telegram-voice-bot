import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from gtts import gTTS

# লোগিং সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# আপনার প্রদান করা টেলিগ্রাম বটের টোকেন
BOT_TOKEN = "8758579077:AAGCfS3EwIm4NkuNk2HmobinSfZZVFaQXTc"

# ব্যবহারকারীর টেক্সট সেভ রাখার ডিকশনারি
user_texts = {}

# ১. /start কমান্ড হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("আসসালামু আলাইকুম! 🎙️ আমাকে যেকোনো লেখা পাঠান, আমি সেটিকে ভয়েজে রূপান্তর করে দেবো।")

# ২. মেসেজ হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    user_texts[user_id] = text
    
    keyboard = [
        [
            InlineKeyboardButton("🇧🇩 বাংলা (Bangla)", callback_data="lang_bn"),
            InlineKeyboardButton("🇺🇸 ইংরেজি (English)", callback_data="lang_en")
        ],
        [
            InlineKeyboardButton("🇮🇳 হিন্দি (Hindi)", callback_data="lang_hi"),
            InlineKeyboardButton("🇸🇦 আরবি (Arabic)", callback_data="lang_ar")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("আপনার লেখাটি পেয়েছি! কোন ভাষায় বা কন্ঠে শুনতে চান সিলেক্ট করুন:", reply_markup=reply_markup)

# জিটিটিএস ফাইল তৈরির ফাংশন (ব্যাকগ্রাউন্ডে চলবে)
def generate_tts(text, lang_code, audio_file):
    tts = gTTS(text=text, lang=lang_code, slow=False)
    tts.save(audio_file)

# ৩. বাটন ক্লিক হ্যান্ডলার
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id not in user_texts:
        await query.edit_message_text("দয়া করে নতুন করে আবার কোনো টেক্সট পাঠান।")
        return

    text = user_texts[user_id]
    data = query.data
    
    lang_code = "bn"
    lang_name = "বাংলা"
    
    if data == "lang_en":
        lang_code = "en"
        lang_name = "ইংরেজি"
    elif data == "lang_hi":
        lang_code = "hi"
        lang_name = "হিন্দি"
    elif data == "lang_ar":
        lang_code = "ar"
        lang_name = "আরবি"
    
    await query.edit_message_text(f"🔄 {lang_name} কন্ঠে ভয়েস তৈরি করা হচ্ছে, একটু অপেক্ষা করুন...")
    
    audio_file = f"voice_{user_id}.mp3"
    try:
        # লোডিং সমস্যা দূর করতে থ্রেডিং ব্যবহার করা হয়েছে
        await asyncio.to_thread(generate_tts, text, lang_code, audio_file)
        
        with open(audio_file, 'rb') as audio:
            await context.bot.send_voice(chat_id=query.message.chat_id, voice=audio, caption=f"🎙️ কন্ঠ: {lang_name}")
            
    except Exception as e:
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"দুঃখিত, ভয়েজ তৈরি করতে সমস্যা হয়েছে: {str(e)}")
    finally:
        # সার্ভার বা স্টোরেজ পরিষ্কার রাখতে ফাইল ডিলিট করা
        if os.path.exists(audio_file):
            os.remove(audio_file)

# ৪. মেইন ফাংশন
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button))

    print("বট সফলভাবে রান হয়েছে এবং অনলাইনে আছে...")
    application.run_polling()

if __name__ == '__main__':
    main()