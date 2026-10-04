import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from gtts import gTTS
from pydub import AudioSegment
from pydub.effects import normalize

# লোগিং সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8758579077:AAGCfS3EwIm4NkuNk2HmobinSfZZVFaQXTc"
user_texts = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "আসসালামু আলাইকুম! 🎙️ আমাকে যেকোনো লেখা পাঠান অথবা বইয়ের কোনো টেক্সট ফাইল (.txt) আপলোড করুন। "
        "আমি সেটিকে ইনহেন্স করে বিভিন্ন কন্ঠে রূপান্তর করে দেবো।"
    )

# সাধারণ টেক্সট হ্যান্ডলার (টেক্সট ইনহেন্সমেন্ট ও ফরম্যাটিং)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    raw_text = update.message.text
    
    # টেক্সট ইনহেন্সমেন্ট: অতিরিক্ত স্পেস বা অপ্রয়োজনীয় ক্যারেক্টার পরিষ্কার করা
    enhanced_text = " ".join(raw_text.strip().split())
    user_texts[user_id] = enhanced_text
    
    keyboard = [
        [
            InlineKeyboardButton("👨‍🦰 সাধারণ পুরুষ (Normal)", callback_data="voice_normal"),
            InlineKeyboardButton("👩 নারী কন্ঠ (Female)", callback_data="voice_female")
        ],
        [
            InlineKeyboardButton("👶 শিশু কন্ঠ (Kid)", callback_data="voice_kid"),
            InlineKeyboardButton("👹 মনস্টার কন্ঠ (Monster)", callback_data="voice_monster")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("✅ আপনার টেক্সট ইনহেন্স করা হয়েছে! কোন কন্ঠে শুনতে চান সিলেক্ট করুন:", reply_markup=reply_markup)

# বই বা টেক্সট ফাইল (Document) হ্যান্ডলার
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    document = update.message.document
    
    if not document.file_name.endswith('.txt'):
        await update.message.reply_text("দুঃখিত, দয়া করে শুধুমাত্র `.txt` ফরম্যাটের বই বা টেক্সট ফাইল আপলোড করুন।")
        return
        
    await update.message.reply_text("📥 বইয়ের ফাইলটি ডাউনলোড ও প্রসেস করা হচ্ছে...")
    
    file = await context.bot.get_file(document.file_id)
    file_path = f"book_{user_id}.txt"
    await file.download_to_drive(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            book_content = f.read()
            
        # টেক্সট ইনহেন্সমেন্ট ও বড় লেখার ক্ষেত্রে সাইজ লিমিট হ্যান্ডেল করা
        enhanced_text = " ".join(book_content.strip().split())
        if len(enhanced_text) > 4000:
            enhanced_text = enhanced_text[:4000] # টেলিগ্রাম লিমিটের জন্য ট্রিম করা
            
        user_texts[user_id] = enhanced_text
        
        keyboard = [
            [
                InlineKeyboardButton("👨‍🦰 সাধারণ পুরুষ (Normal)", callback_data="voice_normal"),
                InlineKeyboardButton("👩 নারী কন্ঠ (Female)", callback_data="voice_female")
            ],
            [
                InlineKeyboardButton("👶 শিশু কন্ঠ (Kid)", callback_data="voice_kid"),
                InlineKeyboardButton("👹 মনস্টার কন্ঠ (Monster)", callback_data="voice_monster")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("✅ বইয়ের লেখা সফলভাবে ইনহেন্স করা হয়েছে! কন্ঠ সিলেক্ট করুন:", reply_markup=reply_markup)
        
    except Exception as e:
        await update.message.reply_text(f"ফাইল পড়তে সমস্যা হয়েছে: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# ভয়েস জেনারেশন এবং অডিও ইনহেন্সমেন্ট (Audio Enhancement) ফাংশন
def generate_enhanced_voice(text, voice_type, output_file):
    temp_file = "temp.mp3"
    tts = gTTS(text=text, lang='bn', slow=False)
    tts.save(temp_file)
    
    # pydub দিয়ে অডিও লোড করা
    sound = AudioSegment.from_mp3(temp_file)
    
    # ভয়েস মডিউলেশন (কন্ঠ পরিবর্তন)
    if voice_type == "voice_female":
        new_sample_rate = int(sound.frame_rate * 1.3)
        sound = sound._spawn(sound.raw_data, override_frame_rate=new_sample_rate)
        sound = sound.set_frame_rate(44100)
    elif voice_type == "voice_kid":
        new_sample_rate = int(sound.frame_rate * 1.5)
        sound = sound._spawn(sound.raw_data, override_frame_rate=new_sample_rate)
        sound = sound.set_frame_rate(44100)
    elif voice_type == "voice_monster":
        new_sample_rate = int(sound.frame_rate * 0.7)
        sound = sound._spawn(sound.raw_data, override_frame_rate=new_sample_rate)
        sound = sound.set_frame_rate(44100)
        
    # অডিও ইনহেন্সমেন্ট (Audio Enhancement & Normalization):
    sound = normalize(sound)
    
    # ফাইনাল ফাইল সেভ করা (উন্নত কোয়ালিটিতে)
    sound.export(output_file, format="mp3", bitrate="192k")
    
    if os.path.exists(temp_file):
        os.remove(temp_file)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id not in user_texts:
        await query.edit_message_text("দয়া করে নতুন করে আবার কোনো টেক্সট বা বই আপলোড করুন।")
        return

    text = user_texts[user_id]
    data = query.data
    
    voice_names = {
        "voice_normal": "সাধারণ পুরুষ কন্ঠ",
        "voice_female": "নারী কন্ঠ",
        "voice_kid": "শিশু কন্ঠ",
        "voice_monster": "মনস্টার কন্ঠ"
    }
    
    selected_name = voice_names.get(data, "কন্ঠ")
    await query.edit_message_text(f"🔄 অডিও ইনহেন্স ও {selected_name} তৈরি করা হচ্ছে, একটু অপেক্ষা করুন...")
    
    audio_file = f"voice_{user_id}.mp3"
    try:
        await asyncio.to_thread(generate_enhanced_voice, text, data, audio_file)
        
        with open(audio_file, 'rb') as audio:
            await context.bot.send_voice(
                chat_id=query.message.chat_id, 
                voice=audio, 
                caption=f"🎙️ ইনহেন্সড ভয়েস ({selected_name})"
            )
            
    except Exception as e:
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"দুঃখিত, ভয়েস তৈরি করতে সমস্যা হয়েছে: {str(e)}")
    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(button))

    print("বট সফলভাবে রান হয়েছে এবং অনলাইনে আছে...")
    application.run_polling()

if __name__ == '__main__':
    main()
