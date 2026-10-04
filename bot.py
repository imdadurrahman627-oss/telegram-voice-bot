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

# ইউজারদের সেটিংস এবং টেক্সট সংরক্ষণের জন্য ডিকশনারি
user_texts = {}
user_settings = {} # ইউজার ভিত্তিক সেটিংস (ভাষা, ভয়েস ইত্যাদি)

# ডিফল্ট সেটিংস পাওয়ার ফাংশন
def get_user_settings(user_id):
    if user_id not in user_settings:
        user_settings[user_id] = {
            "lang": "bn",          # ডিফল্ট ভাষা: বাংলা
            "voice": "voice_normal" # ডিফল্ট ভয়েস
        }
    return user_settings[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    get_user_settings(user_id)
    
    keyboard = [
        [InlineKeyboardButton("⚙️ সেটিংস ও মেনু প্যানেল", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "আসসালামু আলাইকুম! 🎙️ আমাকে যেকোনো লেখা পাঠান অথবা বইয়ের কোনো টেক্সট ফাইল (.txt) আপলোড করুন।\n\n"
        "নিচের **সেটিংস ও মেনু প্যানেল** বাটনে ক্লিক করে ভাষা, ভয়েস টাইপ এবং অন্যান্য অপশন পরিবর্তন করতে পারবেন।",
        reply_markup=reply_markup
    )

# মেইন মেনু বা সেটিংস প্যানেল দেখানোর ফাংশন
async def show_main_menu(query, user_id):
    settings = get_user_settings(user_id)
    lang_name = "বাংলা (Bangla)" if settings["lang"] == "bn" else "ইংরেজি (English)"
    
    voice_names = {
        "voice_normal": "সাধারণ পুরুষ (Normal)",
        "voice_female": "নারী কন্ঠ (Female)",
        "voice_kid": "শিশু কন্ঠ (Kid)",
        "voice_monster": "মনস্টার কন্ঠ (Monster)"
    }
    current_voice = voice_names.get(settings["voice"], "সাধারণ পুরুষ")
    
    keyboard = [
        [InlineKeyboardButton(f"🌐 ভাষা পরিবর্তন: {lang_name}", callback_data="menu_language")],
        [InlineKeyboardButton(f"🗣️ ভয়েস পরিবর্তন: {current_voice}", callback_data="menu_voices")],
        [InlineKeyboardButton("✨ টেক্সট ইনহেন্সমেন্ট স্ট্যাটাস", callback_data="menu_enhance_info")],
        [InlineKeyboardButton("ℹ️ সাহায্য ও নির্দেশনা", callback_data="menu_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🎛️ **বট কন্ট্রোল ও সেটিংস মেনু**\n\n"
        "আপনার পছন্দের অপশনটি নিচে থেকে সিলেক্ট করুন:"
    )
    
    if query.message:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# কলব্যাক হ্যান্ডলার (মেনু এবং বাটন ক্লিক কন্ট্রোল)
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    settings = get_user_settings(user_id)
    
    if data == "main_menu":
        await show_main_menu(query, user_id)
        
    elif data == "menu_language":
        keyboard = [
            [InlineKeyboardButton("🇧🇩 বাংলা (Bangla)", callback_data="set_lang_bn")],
            [InlineKeyboardButton("🇬🇧 ইংরেজি (English)", callback_data="set_lang_en")],
            [InlineKeyboardButton("🔙 মূল মেনুতে ফিরুন", callback_data="main_menu")]
        ]
        await query.edit_message_text("🌐 ভয়েসের জন্য ভাষা নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif data.startswith("set_lang_"):
        lang_code = data.split("_")[2]
        settings["lang"] = lang_code
        lang_str = "বাংলা" if lang_code == "bn" else "ইংরেজি"
        await query.edit_message_text(f"✅ ভাষা সফলভাবে **{lang_str}** করা হয়েছে!", parse_mode="Markdown")
        await asyncio.sleep(1)
        await show_main_menu(query, user_id)
        
    elif data == "menu_voices":
        keyboard = [
            [InlineKeyboardButton("👨‍‍🦰 সাধারণ পুরুষ (Normal)", callback_data="set_voice_normal")],
            [InlineKeyboardButton("👩 নারী কন্ঠ (Female)", callback_data="set_voice_female")],
            [InlineKeyboardButton("👶 শিশু কন্ঠ (Kid)", callback_data="set_voice_kid")],
            [InlineKeyboardButton("👹 মনস্টার কন্ঠ (Monster)", callback_data="set_voice_monster")],
            [InlineKeyboardButton("🔙 মূল মেনুতে ফিরুন", callback_data="main_menu")]
        ]
        await query.edit_message_text("🗣️ আপনার পছন্দের ভয়েস টাইপ সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif data.startswith("set_voice_"):
        voice_type = data.replace("set_", "")
        settings["voice"] = voice_type
        await query.edit_message_text("✅ ডিফল্ট ভয়েস সফলভাবে আপডেট করা হয়েছে!", parse_mode="Markdown")
        await asyncio.sleep(1)
        await show_main_menu(query, user_id)
        
    elif data == "menu_enhance_info":
        keyboard = [[InlineKeyboardButton("🔙 মূল মেনুতে ফিরুন", callback_data="main_menu")]]
        await query.edit_message_text(
            "✨ **টেক্সট ইনহেন্সমেন্ট তথ্য:**\n\n"
            "আপনি যখনই কোনো লেখা বা বই পাঠান, বট স্বয়ংক্রয়ভাবে অতিরিক্ত স্পেস বা অপ্রয়োজনীয় ফরম্যাটিং পরিষ্কার করে অডিও কোয়ালিটি সেরা করার জন্য টেক্সট ইনহেন্স করে নেয়। এটি স্বয়ংক্রিয়ভাবে কাজ করে!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    elif data == "menu_help":
        keyboard = [[InlineKeyboardButton("🔙 মূল মেনুতে ফিরুন", callback_data="main_menu")]]
        await query.edit_message_text(
            "ℹ️ **সাহায্যিকা:**\n\n"
            "১. যেকোনো টেক্সট মেসেজ পাঠান বা `.txt` ফাইল আপলোড করুন।\n"
            "২. সেটিংসে গিয়ে ভাষা ও ভয়েস পরিবর্তন করতে পারবেন।\n"
            "৩. অডিও ফাইল তৈরি হলে সরাসরি ভয়েস মেসেজ আকারে পেয়ে যাবেন।",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    elif data.startswith("voice_direct_"):
        # সরাসরি টেক্সট পাঠানোর পর ইনস্ট্যান্ট ভয়েস জেনারেট করার জন্য
        voice_type = data.replace("voice_direct_", "")
        if user_id not in user_texts:
            await query.edit_message_text("দয়া করে নতুন করে আবার কোনো টেক্সট বা বই পাঠান।")
            return

        text = user_texts[user_id]
        lang = settings["lang"]
        
        voice_names = {
            "voice_normal": "সাধারণ পুরুষ কন্ঠ",
            "voice_female": "নারী কন্ঠ",
            "voice_kid": "শিশু কন্ঠ",
            "voice_monster": "মনস্টার কন্ঠ"
        }
        selected_name = voice_names.get(voice_type, "কন্ঠ")
        
        await query.edit_message_text(f"🔄 অডিও ইনহেন্স ও {selected_name} তৈরি করা হচ্ছে, একটু অপেক্ষা করুন...")
        
        audio_file = f"voice_{user_id}.mp3"
        try:
            await asyncio.to_thread(generate_enhanced_voice, text, lang, voice_type, audio_file)
            
            with open(audio_file, 'rb') as audio:
                await context.bot.send_voice(
                    chat_id=query.message.chat_id, 
                    voice=audio, 
                    caption=f"🎙️ ইনহেন্সড ভয়েস ({selected_name})"
                )
            
            # আবার মেনু দেখানোর অপশন বা রিমাইন্ডার দেওয়া যেতে পারে
            keyboard = [[InlineKeyboardButton("⚙️ সেটিংস মেনু", callback_data="main_menu")]]
            await context.bot.send_message(chat_id=query.message.chat_id, text="অন্যান্য সেটিংস পরিবর্তন করতে চাইলে মেনু ব্যবহার করুন:", reply_markup=InlineKeyboardMarkup(keyboard))
                
        except Exception as e:
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"দুঃখিত, ভয়েস তৈরি করতে সমস্যা হয়েছে: {str(e)}")
        finally:
            if os.path.exists(audio_file):
                os.remove(audio_file)

# সাধারণ টেক্সট হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    raw_text = update.message.text
    
    # টেক্সট ইনহেন্সমেন্ট
    enhanced_text = " ".join(raw_text.strip().split())
    user_texts[user_id] = enhanced_text
    
    keyboard = [
        [
            InlineKeyboardButton("👨‍🦰 সাধারণ পুরুষ", callback_data="voice_direct_voice_normal"),
            InlineKeyboardButton("👩 নারী কন্ঠ", callback_data="voice_direct_voice_female")
        ],
        [
            InlineKeyboardButton("👶 শিশু কন্ঠ", callback_data="voice_direct_voice_kid"),
            InlineKeyboardButton("👹 মনস্টার", callback_data="voice_direct_voice_monster")
        ],
        [
            InlineKeyboardButton("⚙️ সেটিংস মেনু খুলুন", callback_data="main_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "✅ আপনার টেক্সট সফলভাবে ইনহেন্স করা হয়েছে!\nকোন কন্ঠে অডিও শুনতে চান সিলেক্ট করুন অথবা সেটিংস পরিবর্তন করুন:", 
        reply_markup=reply_markup
    )

# টেক্সট ফাইল বা ডকুমেন্ট হ্যান্ডলার
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
            
        enhanced_text = " ".join(book_content.strip().split())
        if len(enhanced_text) > 4000:
            enhanced_text = enhanced_text[:4000]
            
        user_texts[user_id] = enhanced_text
        
        keyboard = [
            [
                InlineKeyboardButton("👨‍🦰 সাধারণ পুরুষ", callback_data="voice_direct_voice_normal"),
                InlineKeyboardButton("👩 নারী কন্ঠ", callback_data="voice_direct_voice_female")
            ],
            [
                InlineKeyboardButton("👶 শিশু কন্ঠ", callback_data="voice_direct_voice_kid"),
                InlineKeyboardButton("👹 মনস্টার", callback_data="voice_direct_voice_monster")
            ],
            [
                InlineKeyboardButton("⚙️ সেটিংস মেনু খুলুন", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("✅ বইয়ের লেখা সফলভাবে ইনহেন্স করা হয়েছে! কন্ঠ সিলেক্ট করুন:", reply_markup=reply_markup)
        
    except Exception as e:
        await update.message.reply_text(f"ফাইল পড়তে সমস্যা হয়েছে: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# ভয়েস জেনারেশন এবং অডিও ইনহেন্সমেন্ট ফাংশন
def generate_enhanced_voice(text, lang, voice_type, output_file):
    temp_file = "temp.mp3"
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(temp_file)
    
    sound = AudioSegment.from_mp3(temp_file)
    
    # ভয়েস মডিউলেশন
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
        sound.set_frame_rate(44100)
        
    # অডিও ইনহেন্সমেন্ট ও নরমালাইজেশন
    sound = normalize(sound)
    sound.export(output_file, format="mp3", bitrate="192k")
    
    if os.path.exists(temp_file):
        os.remove(temp_file)

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(button))

    print("বট সফলভাবে রান হয়েছে এবং মেনু সিস্টেম সহ অনলাইনে আছে...")
    application.run_polling()

if __name__ == '__main__':
    main()
