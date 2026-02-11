"""
O'qtuvchi uchun Test Tekshiruvchi Telegram Bot
Bu bot orqali o'qituvchilar test yaratish, talabalardan javob olish va natijalarni ko'rish mumkin
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
import json
import os
from datetime import datetime

# Bot Token - Bu yerga o'z bot tokeningizni qo'ying
BOT_TOKEN = "8583732852:AAE9jIiZ9urIXv1AHY-9h_1QQQdrP9FgQ9I"

# Holatlar
CREATING_TEST, ADD_QUESTION, ADD_OPTIONS, ADD_ANSWER, TAKING_TEST = range(5)

# Ma'lumotlar saqlash
TESTS_FILE = "tests.json"
RESULTS_FILE = "results.json"

# Admin ID - O'qituvchi ID
ADMIN_ID = 7244207532  # Bu yerga o'z Telegram ID ni qo'ying

def load_data(filename):
    """Fayldan ma'lumotlarni yuklash"""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(filename, data):
    """Ma'lumotlarni faylga saqlash"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot boshlanganda chiqadigan xabar"""
    user_id = update.effective_user.id
    
    if user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("📝 Yangi test yaratish", callback_data="create_test")],
            [InlineKeyboardButton("📊 Natijalarni ko'rish", callback_data="view_results")],
            [InlineKeyboardButton("📋 Testlar ro'yxati", callback_data="list_tests")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Assalomu alaykum, O'qituvchi!\n\n"
            "Nima qilishni xohlaysiz?",
            reply_markup=reply_markup
        )
    else:
        tests = load_data(TESTS_FILE)
        if tests:
            keyboard = [[InlineKeyboardButton(f"📝 {name}", callback_data=f"test_{test_id}")] 
                       for test_id, name in tests.items()]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Assalomu alaykum!\n\n"
                "Mavjud testlardan birini tanlang:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "Assalomu alaykum!\n\n"
                "Hozircha hech qanday test mavjud emas."
            )

# Test yaratish
async def create_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi test yaratishni boshlash"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.edit_message_text("Kechirasiz, siz test yarata olmaysiz.")
        return ConversationHandler.END
    
    await query.edit_message_text(
        "📝 Yangi test yaratish\n\n"
        "Test nomini kiriting:"
    )
    return CREATING_TEST

async def test_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test nomini qabul qilish"""
    test_name = update.message.text
    test_id = str(datetime.now().timestamp()).replace('.', '')
    
    context.user_data['current_test'] = {
        'id': test_id,
        'name': test_name,
        'questions': []
    }
    
    keyboard = [
        [InlineKeyboardButton("➕ Savol qo'shish", callback_data="add_question")],
        [InlineKeyboardButton("✅ Testni saqlash", callback_data="save_test")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Test nomi: {test_name}\n\n"
        "Nima qilishni xohlaysiz?",
        reply_markup=reply_markup
    )
    return CREATING_TEST

async def add_question_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Savol qo'shish uchun so'rash"""
    query = update.callback_query
    await query.answer()
    
    question_num = len(context.user_data['current_test']['questions']) + 1
    await query.edit_message_text(
        f"❓ Savol #{question_num}\n\n"
        "Savol matnini kiriting:"
    )
    return ADD_QUESTION

async def question_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Savolni qabul qilish"""
    question_text = update.message.text
    context.user_data['current_question'] = {
        'question': question_text,
        'options': []
    }
    
    await update.message.reply_text(
        "📝 Javob variantlarini kiriting\n"
        "(Har bir variantni alohida xabarda yuboring)\n\n"
        "Masalan:\n"
        "A) Birinchi variant\n"
        "B) Ikkinchi variant\n\n"
        "Variantlarni yozib bo'lgach, /done yozing"
    )
    return ADD_OPTIONS

async def option_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Javob variantini qabul qilish"""
    option_text = update.message.text
    
    if option_text == '/done':
        if len(context.user_data['current_question']['options']) < 2:
            await update.message.reply_text(
                "⚠️ Kamida 2 ta variant bo'lishi kerak!\n"
                "Yana variantlar kiriting yoki /done yozing"
            )
            return ADD_OPTIONS
        
        keyboard = []
        for i, opt in enumerate(context.user_data['current_question']['options']):
            keyboard.append([InlineKeyboardButton(opt, callback_data=f"answer_{i}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "✅ To'g'ri javobni tanlang:",
            reply_markup=reply_markup
        )
        return ADD_ANSWER
    
    context.user_data['current_question']['options'].append(option_text)
    await update.message.reply_text(
        f"✅ Variant qo'shildi ({len(context.user_data['current_question']['options'])})\n\n"
        "Yana variant kiriting yoki /done yozing"
    )
    return ADD_OPTIONS

async def answer_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """To'g'ri javobni saqlash"""
    query = update.callback_query
    await query.answer()
    
    answer_index = int(query.data.split('_')[1])
    context.user_data['current_question']['correct_answer'] = answer_index
    
    # Savolni testga qo'shish
    context.user_data['current_test']['questions'].append(context.user_data['current_question'])
    
    keyboard = [
        [InlineKeyboardButton("➕ Yana savol qo'shish", callback_data="add_question")],
        [InlineKeyboardButton("✅ Testni saqlash", callback_data="save_test")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    questions_count = len(context.user_data['current_test']['questions'])
    await query.edit_message_text(
        f"✅ Savol qo'shildi!\n\n"
        f"Jami savollar: {questions_count}\n\n"
        "Nima qilishni xohlaysiz?",
        reply_markup=reply_markup
    )
    return CREATING_TEST

async def save_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Testni saqlash"""
    query = update.callback_query
    await query.answer()
    
    current_test = context.user_data['current_test']
    
    if len(current_test['questions']) == 0:
        await query.edit_message_text(
            "⚠️ Test bo'sh! Kamida 1 ta savol qo'shing.\n"
            "Qaytadan /start buyrug'ini yuboring."
        )
        return ConversationHandler.END
    
    tests = load_data(TESTS_FILE)
    tests[current_test['id']] = current_test['name']
    save_data(TESTS_FILE, tests)
    
    # Test tafsilotlarini saqlash
    test_details_file = f"test_{current_test['id']}.json"
    save_data(test_details_file, current_test)
    
    await query.edit_message_text(
        f"✅ Test muvaffaqiyatli saqlandi!\n\n"
        f"Test nomi: {current_test['name']}\n"
        f"Savollar soni: {len(current_test['questions'])}\n\n"
        "Qaytadan /start buyrug'ini yuboring."
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bekor qilish"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Amal bekor qilindi.\n\nQaytadan /start buyrug'ini yuboring.")
    return ConversationHandler.END

# Test topshirish
async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Testni boshlash"""
    query = update.callback_query
    await query.answer()
    
    test_id = query.data.replace('test_', '')
    test_details_file = f"test_{test_id}.json"
    
    if not os.path.exists(test_details_file):
        await query.edit_message_text("⚠️ Test topilmadi!")
        return
    
    test_data = load_data(test_details_file)
    context.user_data['active_test'] = {
        'test_id': test_id,
        'test_data': test_data,
        'current_question': 0,
        'answers': []
    }
    
    await show_question(query, context)
    return TAKING_TEST

async def show_question(query_or_update, context: ContextTypes.DEFAULT_TYPE):
    """Savolni ko'rsatish"""
    test_info = context.user_data['active_test']
    current_q = test_info['current_question']
    question_data = test_info['test_data']['questions'][current_q]
    
    keyboard = []
    for i, option in enumerate(question_data['options']):
        keyboard.append([InlineKeyboardButton(option, callback_data=f"ans_{i}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"📝 {test_info['test_data']['name']}\n\n"
        f"Savol {current_q + 1}/{len(test_info['test_data']['questions'])}\n\n"
        f"❓ {question_data['question']}\n\n"
        "Javobni tanlang:"
    )
    
    if hasattr(query_or_update, 'edit_message_text'):
        await query_or_update.edit_message_text(text, reply_markup=reply_markup)
    else:
        await query_or_update.message.reply_text(text, reply_markup=reply_markup)

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Javobni qabul qilish"""
    query = update.callback_query
    await query.answer()
    
    answer_index = int(query.data.replace('ans_', ''))
    test_info = context.user_data['active_test']
    test_info['answers'].append(answer_index)
    test_info['current_question'] += 1
    
    if test_info['current_question'] < len(test_info['test_data']['questions']):
        await show_question(query, context)
        return TAKING_TEST
    else:
        # Test tugadi, natijani hisoblash
        correct = 0
        total = len(test_info['test_data']['questions'])
        
        for i, question in enumerate(test_info['test_data']['questions']):
            if test_info['answers'][i] == question['correct_answer']:
                correct += 1
        
        percentage = (correct / total) * 100
        
        # Natijani saqlash
        results = load_data(RESULTS_FILE)
        user_id = str(update.effective_user.id)
        if user_id not in results:
            results[user_id] = []
        
        results[user_id].append({
            'test_id': test_info['test_id'],
            'test_name': test_info['test_data']['name'],
            'correct': correct,
            'total': total,
            'percentage': percentage,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_name': update.effective_user.full_name
        })
        save_data(RESULTS_FILE, results)
        
        await query.edit_message_text(
            f"✅ Test yakunlandi!\n\n"
            f"Test: {test_info['test_data']['name']}\n"
            f"To'g'ri javoblar: {correct}/{total}\n"
            f"Foiz: {percentage:.1f}%\n\n"
            f"Qaytadan /start buyrug'ini yuboring."
        )
        return ConversationHandler.END

async def view_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Natijalarni ko'rish"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.edit_message_text("Kechirasiz, siz natijalarni ko'ra olmaysiz.")
        return
    
    results = load_data(RESULTS_FILE)
    
    if not results:
        await query.edit_message_text("Hozircha hech qanday natija yo'q.")
        return
    
    text = "📊 Test natijalari:\n\n"
    for user_id, user_results in results.items():
        text += f"👤 Talaba: {user_results[-1]['user_name']}\n"
        for result in user_results[-3:]:  # Oxirgi 3 ta natija
            text += (
                f"  📝 {result['test_name']}\n"
                f"  ✅ {result['correct']}/{result['total']} ({result['percentage']:.1f}%)\n"
                f"  📅 {result['date']}\n\n"
            )
    
    await query.edit_message_text(text[:4000])  # Telegram limit

async def list_tests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Testlar ro'yxatini ko'rsatish"""
    query = update.callback_query
    await query.answer()
    
    tests = load_data(TESTS_FILE)
    
    if not tests:
        await query.edit_message_text("Hozircha hech qanday test yo'q.")
        return
    
    text = "📋 Mavjud testlar:\n\n"
    for test_id, test_name in tests.items():
        test_details = load_data(f"test_{test_id}.json")
        text += f"📝 {test_name}\n"
        text += f"   Savollar: {len(test_details['questions'])}\n\n"
    
    await query.edit_message_text(text)

def main():
    """Botni ishga tushirish"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Test yaratish ConversationHandler
    create_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_test, pattern="^create_test$")],
        states={
            CREATING_TEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, test_name_received),
                CallbackQueryHandler(add_question_prompt, pattern="^add_question$"),
                CallbackQueryHandler(save_test, pattern="^save_test$"),
                CallbackQueryHandler(cancel, pattern="^cancel$")
            ],
            ADD_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, question_received)
            ],
            ADD_OPTIONS: [
                MessageHandler(filters.TEXT, option_received)
            ],
            ADD_ANSWER: [
                CallbackQueryHandler(answer_selected, pattern="^answer_")
            ]
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")]
    )
    
    # Test topshirish ConversationHandler
    test_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_test, pattern="^test_")],
        states={
            TAKING_TEST: [
                CallbackQueryHandler(answer_question, pattern="^ans_")
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(create_conv)
    application.add_handler(test_conv)
    application.add_handler(CallbackQueryHandler(view_results, pattern="^view_results$"))
    application.add_handler(CallbackQueryHandler(list_tests, pattern="^list_tests$"))
    
    print("Bot ishga tushdi...")
    application.run_polling()

if __name__ == '__main__':

    main()
