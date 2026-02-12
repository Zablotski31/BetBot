import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from database import get_connection, init_database, export_to_excel, import_from_excel, create_template
from handlers import (
    add_bet_start, select_bettor, select_sport, select_bet_type,
    enter_event, enter_selection, enter_odds, enter_stake,
    confirm_bet, cancel, main_menu, help_command,  # <--- ДОБАВЛЕНЫ main_menu и help_command
    active_bets, bet_history, set_result, bettor_stats, delete_bet,
    delete_bettor, delete_bettor_callback,
    SELECT_BETTOR, SELECT_SPORT, SELECT_BET_TYPE, ENTER_EVENT,
    ENTER_SELECTION, ENTER_ODDS, ENTER_STAKE, CONFIRM_BET
)
from datetime import datetime
import os

# ВСТАВЬ СВОЙ ТОКЕН
TOKEN = "8046876619:AAFxFAgUp-m1LAbH5duUOJt7Uk0jIXAj1pQ"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение с меню"""
    await main_menu(update, context)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню"""
    await main_menu(update, context)

async def add_bettor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить нового беттора (Имя Фамилия)"""
    if not context.args:
        await update.message.reply_text(
            "❌ Нужно написать имя и фамилию.\n"
            "Пример: /add_bettor Антон Петров"
        )
        return
    
    full_name = ' '.join(context.args)
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO bettors (full_name) VALUES (?)', (full_name,))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(f"✅ Беттор добавлен:\n👤 {full_name}")
        await main_menu(update, context)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def list_bettors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать всех бетторов"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            b.id, 
            b.full_name,
            COUNT(bets.id) as bets_count
        FROM bettors b
        LEFT JOIN bets ON b.id = bets.bettor_id
        GROUP BY b.id
        ORDER BY b.full_name
    ''')
    bettors = cursor.fetchall()
    conn.close()
    
    if not bettors:
        await update.message.reply_text("📭 Пока нет ни одного беттора.")
        await main_menu(update, context)
        return
    
    text = "📋 *СПИСОК БЕТТОРОВ:*\n\n"
    
    for b in bettors:
        text += f"🆔 *{b['id']}* | 👤 {b['full_name']}\n"
        text += f"   📊 Ставок: {b['bets_count']}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')
    
    keyboard = [
        [KeyboardButton("❌ Удалить беттора")],
        [KeyboardButton("🏠 Главное меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=reply_markup
    )

async def export_bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экспорт всех ставок в Excel"""
    
    msg = await update.message.reply_text("📤 Экспортирую данные...")
    
    try:
        filename = export_to_excel()
        
        with open(filename, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=filename,
                caption="✅ Экспорт завершен!\n"
                       "Все ставки и справочники сохранены в Excel."
            )
        
        os.remove(filename)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка экспорта: {e}")
    
    keyboard = [[KeyboardButton("🏠 Главное меню")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)

async def import_bets_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало импорта ставок"""
    
    await update.message.reply_text(
        "📥 *Импорт ставок из Excel*\n\n"
        "Отправьте файл Excel в формате:\n"
        "• Лист с названием 'Ставки'\n"
        "• Колонки: беттор, вид_спорта, тип_ставки, событие, выбор, "
        "коэффициент, сумма, статус, прибыль, дата_создания, дата_расчета\n\n"
        "Хотите скачать шаблон?",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📎 Скачать шаблон", callback_data="get_template")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_import")]
        ])
    )

async def import_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка загруженного Excel файла"""
    
    if not update.message.document:
        return
    
    file = update.message.document
    
    if not file.file_name.endswith(('.xlsx', '.xls')):
        await update.message.reply_text("❌ Пожалуйста, отправьте файл Excel (.xlsx или .xls)")
        return
    
    msg = await update.message.reply_text("📥 Импортирую данные...")
    
    try:
        file_obj = await file.get_file()
        file_path = f"import_{file.file_name}"
        await file_obj.download_to_drive(file_path)
        
        imported, errors = import_from_excel(file_path)
        
        os.remove(file_path)
        
        await update.message.reply_text(
            f"✅ *Импорт завершен!*\n\n"
            f"📥 Импортировано ставок: {imported}\n"
            f"❌ Ошибок: {errors}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка импорта: {e}")
    
    keyboard = [[KeyboardButton("🏠 Главное меню")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка инлайн кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "get_template":
        filename = create_template()
        with open(filename, 'rb') as f:
            await query.message.reply_document(
                document=f,
                filename=filename,
                caption="📎 Шаблон для импорта ставок"
            )
        os.remove(filename)
        
    elif query.data == "cancel_import":
        await query.message.edit_text("❌ Импорт отменен")
        
        keyboard = [[KeyboardButton("🏠 Главное меню")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await query.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    text = update.message.text
    
    if text == "🎯 Добавить ставку":
        await add_bet_start(update, context)
        
    elif text == "📊 Активные ставки":
        await active_bets(update, context)
        
    elif text == "📜 История":
        await bet_history(update, context)
        
    elif text == "👤 Бетторы":
        await list_bettors(update, context)
        
    elif text == "📈 Статистика":
        await bettor_stats(update, context)
        
    elif text == "❌ Удалить беттора":
        await update.message.reply_text(
            "🗑 *Удаление беттора*\n\n"
            "Введите ID беттора для удаления:\n"
            "Пример: 3\n\n"
            "Список бетторов: /bettors",
            parse_mode='Markdown'
        )
        context.user_data['awaiting_bettor_delete'] = True
        
    elif text == "🗑 Удалить ставку":
        await update.message.reply_text(
            "🗑 *Удаление ставки*\n\n"
            "Введите ID ставки для удаления:\n"
            "Пример: /delete 5\n\n"
            "Список активных ставок: /active",
            parse_mode='Markdown'
        )
        
    elif text == "📤 Экспорт Excel":
        await export_bets(update, context)
        
    elif text == "📥 Импорт Excel":
        await import_bets_start(update, context)
        
    elif text == "❓ Помощь":
        await help_command(update, context)
        
    elif text == "🏠 Главное меню":
        await main_menu(update, context)
        
    # Проверяем, ждем ли мы ID для удаления беттора
    elif context.user_data.get('awaiting_bettor_delete'):
        try:
            bettor_id = int(text)
            context.user_data['awaiting_bettor_delete'] = False
            context.args = [str(bettor_id)]
            await delete_bettor(update, context)
        except ValueError:
            context.user_data['awaiting_bettor_delete'] = False
            await update.message.reply_text("❌ Введите число!")
            
    else:
        await update.message.reply_text("❌ Неизвестная команда")

def main():
    """Запуск бота"""
    init_database()
    
    app = Application.builder().token(TOKEN).build()
    
    # --- Обычные команды ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("add_bettor", add_bettor))
    app.add_handler(CommandHandler("bettors", list_bettors))
    
    # --- Команды для работы со ставками ---
    app.add_handler(CommandHandler("active", active_bets))
    app.add_handler(CommandHandler("history", bet_history))
    app.add_handler(CommandHandler("result", set_result))
    app.add_handler(CommandHandler("stats", bettor_stats))
    app.add_handler(CommandHandler("delete", delete_bet))
    
    # --- Команды для управления бетторами ---
    app.add_handler(CommandHandler("delete_bettor", delete_bettor))
    app.add_handler(CallbackQueryHandler(delete_bettor_callback, pattern="^(force_delete_bettor_|cancel_delete_bettor)$"))
    
    # --- Команды экспорта/импорта ---
    app.add_handler(CommandHandler("export", export_bets))
    app.add_handler(CommandHandler("import", import_bets_start))
    
    # --- Обработчик файлов (для импорта Excel) ---
    app.add_handler(MessageHandler(filters.Document.ALL, import_file_handler))
    
    # --- Обработчик инлайн кнопок ---
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^(get_template|cancel_import)$"))
    
    # --- Обработчик кнопок меню ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    
    # --- ConversationHandler для добавления ставки ---
    add_bet_handler = ConversationHandler(
        entry_points=[
            CommandHandler("add_bet", add_bet_start),
            MessageHandler(filters.Regex("^🎯 Добавить ставку$"), add_bet_start)
        ],
        states={
            SELECT_BETTOR: [CallbackQueryHandler(select_bettor, pattern="^bettor_")],
            SELECT_SPORT: [CallbackQueryHandler(select_sport, pattern="^sport_")],
            SELECT_BET_TYPE: [CallbackQueryHandler(select_bet_type, pattern="^bettype_")],
            ENTER_EVENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_event)],
            ENTER_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_selection)],
            ENTER_ODDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_odds)],
            ENTER_STAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_stake)],
            CONFIRM_BET: [CallbackQueryHandler(confirm_bet, pattern="^confirm_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(add_bet_handler)
    
    print("✅ Бот запущен! Иди в Telegram и пиши /start")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()