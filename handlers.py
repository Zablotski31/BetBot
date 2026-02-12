from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import get_connection
from datetime import datetime

# Состояния для диалога добавления ставки
(
    SELECT_BETTOR,
    SELECT_SPORT,
    SELECT_BET_TYPE,
    ENTER_EVENT,
    ENTER_SELECTION,
    ENTER_ODDS,
    ENTER_STAKE,
    CONFIRM_BET
) = range(8)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню с кнопками"""
    
    keyboard = [
        [KeyboardButton("🎯 Добавить ставку")],
        [KeyboardButton("📊 Активные ставки"), KeyboardButton("📜 История")],
        [KeyboardButton("👤 Бетторы"), KeyboardButton("📈 Статистика")],
        [KeyboardButton("❌ Удалить беттора"), KeyboardButton("🗑 Удалить ставку")],
        [KeyboardButton("📤 Экспорт Excel"), KeyboardButton("📥 Импорт Excel")],
        [KeyboardButton("❓ Помощь")]
    ]
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    await update.message.reply_text(
        "👋 *Главное меню*\n\n"
        "Выберите действие:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка с кнопкой меню"""
    
    keyboard = [
        [KeyboardButton("🏠 Главное меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "📚 ДОСТУПНЫЕ КОМАНДЫ:\n\n"
        
        "👤 Управление бетторами:\n"
        "/add_bettor Имя Фамилия - добавить игрока\n"
        "/bettors - список всех бетторов\n"
        "/delete_bettor ID - удалить беттора\n\n"
        
        "🎯 Добавление ставок:\n"
        "/add_bet - пошаговое добавление ставки\n\n"
        
        "📊 Просмотр ставок:\n"
        "/active - активные ставки (в ожидании)\n"
        "/history - история рассчитанных ставок\n"
        "/stats - статистика по бетторам\n\n"
        
        "⚡️ Управление ставками:\n"
        "/result ID выигрыш - отметить выигрыш\n"
        "/result ID проигрыш - отметить проигрыш\n"
        "/result ID возврат - отметить возврат\n"
        "/delete ID - удалить ставку\n\n"
        
        "📁 Excel:\n"
        "/export - экспорт всех данных в Excel\n"
        "/import - импорт ставок из Excel\n\n"
        
        "🔧 Другое:\n"
        "/start - главное меню\n"
        "/menu - показать меню\n"
        "/help - эта справка",
        reply_markup=reply_markup
    )

async def add_bet_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления ставки - выбор беттора"""
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, full_name FROM bettors ORDER BY full_name')
    bettors = cursor.fetchall()
    conn.close()
    
    if not bettors:
        await update.message.reply_text(
            "❌ Сначала добавьте бетторов!\n"
            "Используйте /add_bettor Имя Фамилия"
        )
        return ConversationHandler.END
    
    keyboard = []
    for b in bettors:
        keyboard.append([InlineKeyboardButton(
            f"{b['full_name']}", 
            callback_data=f"bettor_{b['id']}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👤 Выберите беттора:",
        reply_markup=reply_markup
    )
    
    return SELECT_BETTOR

async def select_bettor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора беттора"""
    query = update.callback_query
    await query.answer()
    bettor_id = int(query.data.split('_')[1])
    context.user_data['bettor_id'] = bettor_id
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT full_name FROM bettors WHERE id = ?', (bettor_id,))
    bettor = cursor.fetchone()
    conn.close()
    
    await query.edit_message_text(
        f"✅ Выбран беттор: {bettor['full_name']}\n\n"
        f"Теперь выберите вид спорта:"
    )
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM sports ORDER BY name')
    sports = cursor.fetchall()
    conn.close()
    
    keyboard = []
    for s in sports:
        keyboard.append([InlineKeyboardButton(
            s['name'], 
            callback_data=f"sport_{s['id']}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        "🏆 Вид спорта:",
        reply_markup=reply_markup
    )
    
    return SELECT_SPORT

async def select_sport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор вида спорта"""
    query = update.callback_query
    await query.answer()
    
    sport_id = int(query.data.split('_')[1])
    context.user_data['sport_id'] = sport_id
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sports WHERE id = ?', (sport_id,))
    sport = cursor.fetchone()
    conn.close()
    
    await query.edit_message_text(
        f"✅ Вид спорта: {sport['name']}\n\n"
        f"Теперь выберите тип ставки:"
    )
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM bet_types ORDER BY name')
    bet_types = cursor.fetchall()
    conn.close()
    
    keyboard = []
    for bt in bet_types:
        keyboard.append([InlineKeyboardButton(
            bt['name'], 
            callback_data=f"bettype_{bt['id']}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        "🎯 Тип ставки:",
        reply_markup=reply_markup
    )
    
    return SELECT_BET_TYPE

async def select_bet_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор типа ставки"""
    query = update.callback_query
    await query.answer()
    
    bet_type_id = int(query.data.split('_')[1])
    context.user_data['bet_type_id'] = bet_type_id
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM bet_types WHERE id = ?', (bet_type_id,))
    bet_type = cursor.fetchone()
    conn.close()
    
    await query.edit_message_text(
        f"✅ Тип ставки: {bet_type['name']}\n\n"
        f"📝 Введите название события:\n"
        f"Например: Реал Мадрид - Барселона"
    )
    
    return ENTER_EVENT

async def enter_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ввод названия события"""
    event_name = update.message.text
    context.user_data['event_name'] = event_name
    
    await update.message.reply_text(
        f"✅ Событие: {event_name}\n\n"
        f"📊 Введите ваш выбор:\n"
        f"Примеры:\n"
        f"• Исход: П1, X, П2\n"
        f"• Тотал: ТБ 2.5, ТМ 3.0\n"
        f"• Фора: Ф1(-1), Ф2(+1.5)\n"
        f"• Точный счет: 2:1, 3:0\n"
        f"• Другой: любой текст"
    )
    
    return ENTER_SELECTION

async def enter_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ввод выбора"""
    selection = update.message.text
    context.user_data['selection'] = selection
    
    await update.message.reply_text(
        f"✅ Выбор: {selection}\n\n"
        f"💰 Введите коэффициент (число):\n"
        f"Например: 1.85 или 2.0"
    )
    
    return ENTER_ODDS

async def enter_odds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ввод коэффициента"""
    try:
        odds = float(update.message.text.replace(',', '.'))
        if odds < 1.0:
            await update.message.reply_text("❌ Коэффициент не может быть меньше 1.0. Введите снова:")
            return ENTER_ODDS
        
        context.user_data['odds'] = odds
        
        await update.message.reply_text(
            f"✅ Коэффициент: {odds}\n\n"
            f"💵 Введите сумму ставки (BYN):\n"
            f"Например: 1000 или 50.50"
        )
        
        return ENTER_STAKE
        
    except ValueError:
        await update.message.reply_text("❌ Введите число (например: 1.85 или 2.0):")
        return ENTER_ODDS

async def enter_stake(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ввод суммы ставки"""
    try:
        stake = float(update.message.text.replace(',', '.'))
        if stake <= 0:
            await update.message.reply_text("❌ Сумма должна быть больше 0. Введите снова:")
            return ENTER_STAKE
        
        context.user_data['stake'] = stake
        
        text = format_bet_summary(context.user_data)
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_yes"),
                InlineKeyboardButton("❌ Отмена", callback_data="confirm_no")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text + "\n\nПодтверждаете ставку?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return CONFIRM_BET
        
    except ValueError:
        await update.message.reply_text("❌ Введите число (например: 1000 или 50.50):")
        return ENTER_STAKE

async def confirm_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение и сохранение ставки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_yes":
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bets 
                (bettor_id, sport_id, bet_type_id, event_name, selection, 
                 odds, stake, status, profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                context.user_data['bettor_id'],
                context.user_data['sport_id'],
                context.user_data['bet_type_id'],
                context.user_data['event_name'],
                context.user_data['selection'],
                context.user_data['odds'],
                context.user_data['stake'],
                'ожидание',
                0
            ))
            
            conn.commit()
            conn.close()
            
            await query.edit_message_text("✅ Ставка успешно добавлена!\nСтатус: ожидание расчета")
            
            keyboard = [[KeyboardButton("🏠 Главное меню")]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await query.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)
            
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка при сохранении: {e}")
    else:
        await query.edit_message_text("❌ Добавление ставки отменено")
        
        keyboard = [[KeyboardButton("🏠 Главное меню")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await query.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена всего диалога с возвратом в меню"""
    
    keyboard = [
        [KeyboardButton("🏠 Главное меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "❌ Добавление ставки отменено",
        reply_markup=reply_markup
    )
    context.user_data.clear()
    return ConversationHandler.END
async def active_bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все активные ставки (в ожидании)"""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            b.id,
            bettors.full_name as bettor_name,
            sports.name as sport_name,
            bet_types.name as bet_type_name,
            b.event_name,
            b.selection,
            b.odds,
            b.stake,
            b.created_at
        FROM bets b
        JOIN bettors ON b.bettor_id = bettors.id
        JOIN sports ON b.sport_id = sports.id
        JOIN bet_types ON b.bet_type_id = bet_types.id
        WHERE b.status = 'ожидание'
        ORDER BY b.created_at DESC
    ''')
    
    bets = cursor.fetchall()
    conn.close()
    
    if not bets:
        await update.message.reply_text("📭 Нет активных ставок (все рассчитаны).")
        keyboard = [[KeyboardButton("🏠 Главное меню")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)
        return
    
    text = "🎯 *АКТИВНЫЕ СТАВКИ:*\n\n"
    
    for bet in bets:
        potential_win = round(bet['stake'] * bet['odds'], 2)
        
        bet_text = (
            f"🆔 *ID:* {bet['id']}\n"
            f"👤 *Беттор:* {bet['bettor_name']}\n"
            f"🏆 *Спорт:* {bet['sport_name']} | 🎯 {bet['bet_type_name']}\n"
            f"📝 *Событие:* {bet['event_name']}\n"
            f"📊 *Выбор:* {bet['selection']} | 💰 *Кэф:* {bet['odds']}\n"
            f"💵 *Сумма:* {bet['stake']} BYN\n"
            f"💰 *Потенциал:* {potential_win} BYN\n"
            f"📅 *Добавлена:* {bet['created_at'][:16]}\n"
            f"⏳ *Статус:* ожидание\n"
            f"{'─' * 30}\n\n"
        )
        
        if len(text + bet_text) > 4000:
            await update.message.reply_text(text, parse_mode='Markdown')
            text = bet_text
        else:
            text += bet_text
    
    if text:
        await update.message.reply_text(text, parse_mode='Markdown')
    
    await update.message.reply_text(
        "📌 *Чтобы рассчитать ставку:*\n"
        "/result ID выигрыш\n"
        "/result ID проигрыш\n"
        "/result ID возврат\n\n"
        "Пример: /result 5 выигрыш",
        parse_mode='Markdown'
    )
    
    keyboard = [[KeyboardButton("🏠 Главное меню")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)

async def bet_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать историю рассчитанных ставок"""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            b.id,
            bettors.full_name as bettor_name,
            sports.name as sport_name,
            bet_types.name as bet_type_name,
            b.event_name,
            b.selection,
            b.odds,
            b.stake,
            b.status,
            b.profit,
            b.updated_at
        FROM bets b
        JOIN bettors ON b.bettor_id = bettors.id
        JOIN sports ON b.sport_id = sports.id
        JOIN bet_types ON b.bet_type_id = bet_types.id
        WHERE b.status != 'ожидание'
        ORDER BY b.updated_at DESC
        LIMIT 20
    ''')
    
    bets = cursor.fetchall()
    conn.close()
    
    if not bets:
        await update.message.reply_text("📭 История ставок пуста.")
        keyboard = [[KeyboardButton("🏠 Главное меню")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)
        return
    text = "📜 *ИСТОРИЯ СТАВОК (последние 20):*\n\n"
    
    for bet in bets:
        if bet['status'] == 'выигрыш':
            status_emoji = "✅"
            win_amount = round(bet['stake'] * bet['odds'], 2)
            result_line = f"💰 *Выигрыш:* {win_amount} BYN (📈 +{bet['profit']} BYN)"
        elif bet['status'] == 'проигрыш':
            status_emoji = "❌"
            result_line = f"💸 *Потеряно:* {bet['stake']} BYN (📉 {bet['profit']} BYN)"
        else:
            status_emoji = "🔄"
            result_line = f"🔄 *Возврат:* {bet['stake']} BYN"
        
        bet_text = (
            f"🆔 *ID:* {bet['id']} {status_emoji}\n"
            f"👤 *Беттор:* {bet['bettor_name']}\n"
            f"🏆 *Спорт:* {bet['sport_name']} | 🎯 {bet['bet_type_name']}\n"
            f"📝 *Событие:* {bet['event_name']}\n"
            f"📊 *Выбор:* {bet['selection']} | 💰 *Кэф:* {bet['odds']}\n"
            f"💵 *Ставка:* {bet['stake']} BYN\n"
            f"{result_line}\n"
            f"📅 *Рассчитана:* {bet['updated_at'][:16]}\n"
            f"{'─' * 30}\n\n"
        )
        
        if len(text + bet_text) > 4000:
            await update.message.reply_text(text, parse_mode='Markdown')
            text = bet_text
        else:
            text += bet_text
    
    if text:
        await update.message.reply_text(text, parse_mode='Markdown')
    
    keyboard = [[KeyboardButton("🏠 Главное меню")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)

async def set_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установить результат ставки: /result ID выигрыш/проигрыш/возврат"""
    
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Неправильный формат!\n"
            "Используйте: /result ID выигрыш\n"
            "Или: /result ID проигрыш\n"
            "Или: /result ID возврат",
            parse_mode='Markdown'
        )
        return
    
    try:
        bet_id = int(context.args[0])
        result = context.args[1].lower()
        
        if result not in ['выигрыш', 'проигрыш', 'возврат']:
            await update.message.reply_text(
                "❌ Статус должен быть: выигрыш, проигрыш или возврат",
                parse_mode='Markdown'
            )
            return
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT odds, stake FROM bets WHERE id = ? AND status = 'ожидание'
        ''', (bet_id,))
        
        bet = cursor.fetchone()
        
        if not bet:
            conn.close()
            await update.message.reply_text(
                f"❌ Ставка с ID {bet_id} не найдена или уже рассчитана!"
            )
            return
        
        odds = bet['odds']
        stake = bet['stake']
        
        if result == 'выигрыш':
            profit = round(stake * (odds - 1), 2)
            win_amount = round(stake * odds, 2)
        elif result == 'проигрыш':
            profit = -stake
            win_amount = 0
        else:
            profit = 0
            win_amount = stake
        
        cursor.execute('''
            UPDATE bets 
            SET status = ?, profit = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (result, profit, bet_id))
        
        conn.commit()
        conn.close()
        
        if result == 'выигрыш':
            emoji = "✅"
            await update.message.reply_text(
                f"{emoji} *Ставка ID {bet_id} рассчитана!*\n"
                f"📊 *Результат:* {result}\n"
                f"💰 *Выигрыш:* {win_amount} BYN\n"
                f"📈 *Прибыль:* +{profit} BYN",
                parse_mode='Markdown'
                )
        elif result == 'проигрыш':
            emoji = "❌"
            await update.message.reply_text(
                f"{emoji} *Ставка ID {bet_id} рассчитана!*\n"
                f"📊 *Результат:* {result}\n"
                f"💸 *Потеряно:* {stake} BYN\n"
                f"📉 *Убыток:* {profit} BYN",
                parse_mode='Markdown'
            )
        else:
            emoji = "🔄"
            await update.message.reply_text(
                f"{emoji} *Ставка ID {bet_id} рассчитана!*\n"
                f"📊 *Результат:* {result}\n"
                f"🔄 *Возврат:* {win_amount} BYN",
                parse_mode='Markdown'
            )
        
        keyboard = [[KeyboardButton("🏠 Главное меню")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)
        
    except ValueError:
        await update.message.reply_text("❌ ID ставки должен быть числом!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def bettor_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику по бетторам"""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            bettors.full_name,
            COUNT(b.id) as total_bets,
            SUM(CASE WHEN b.status = 'выигрыш' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN b.status = 'проигрыш' THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN b.status = 'возврат' THEN 1 ELSE 0 END) as refunds,
            COUNT(CASE WHEN b.status = 'ожидание' THEN 1 END) as pending,
            SUM(b.profit) as total_profit,
            AVG(b.odds) as avg_odds,
            SUM(b.stake) as total_stake
        FROM bettors
        LEFT JOIN bets b ON bettors.id = b.bettor_id
        GROUP BY bettors.id
        ORDER BY total_profit DESC
    ''')
    
    stats = cursor.fetchall()
    conn.close()
    
    if not stats or stats[0]['total_bets'] == 0:
        await update.message.reply_text("📊 Статистики пока нет (нет рассчитанных ставок).")
        keyboard = [[KeyboardButton("🏠 Главное меню")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)
        return
    
    text = "📊 *СТАТИСТИКА БЕТТОРОВ:*\n\n"
    
    for s in stats:
        if s['total_bets'] == 0:
            continue
            
        win_rate = round(s['wins'] / (s['wins'] + s['losses']) * 100, 1) if (s['wins'] + s['losses']) > 0 else 0
        roi = round(s['total_profit'] / s['total_stake'] * 100, 1) if s['total_stake'] > 0 else 0
        
        profit_emoji = "🔥" if s['total_profit'] > 0 else "❄️" if s['total_profit'] < 0 else "➖"
        
        text += (
            f"👤 *{s['full_name']}*\n"
            f"💰 {profit_emoji} Прибыль: {s['total_profit']:.2f} BYN\n"
            f"📊 ROI: {roi}%\n"
            f"🎯 Проходимость: {win_rate}% ({s['wins']}/{s['wins'] + s['losses']})\n"
            f"📈 Всего ставок: {s['total_bets']} "
            f"(✅ {s['wins']} | ❌ {s['losses']} | 🔄 {s['refunds']} | ⏳ {s['pending']})\n"
            f"💰 Средний кэф: {s['avg_odds']:.2f}\n"
            f"{'─' * 30}\n\n"
        )
    
    await update.message.reply_text(text, parse_mode='Markdown')
    
    keyboard = [[KeyboardButton("🏠 Главное меню")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)

async def delete_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить ставку: /delete ID"""
    
    if not context.args:
        await update.message.reply_text("❌ Укажите ID ставки: /delete 5", parse_mode='Markdown')
        return
    
    try:
        bet_id = int(context.args[0])
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM bets WHERE id = ?', (bet_id,))
        if not cursor.fetchone():
            conn.close()
            await update.message.reply_text(f"❌ Ставка с ID {bet_id} не найдена!")
            return
        
        cursor.execute('DELETE FROM bets WHERE id = ?', (bet_id,))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(f"🗑 Ставка ID {bet_id} удалена!")
        
        keyboard = [[KeyboardButton("🏠 Главное меню")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)
        
    except ValueError:
        await update.message.reply_text("❌ ID ставки должен быть числом!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def delete_bettor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить беттора: /delete_bettor ID"""
    
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите ID беттора!\n"
            "/delete_bettor 3\n\n"
            "Список бетторов: /bettors",
            parse_mode='Markdown'
        )
        return
    
    try:
        bettor_id = int(context.args[0])
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT full_name FROM bettors WHERE id = ?', (bettor_id,))
        bettor = cursor.fetchone()
        
        if not bettor:
            conn.close()
            await update.message.reply_text(f"❌ Беттор с ID {bettor_id} не найден!")
            return
        
        cursor.execute('SELECT COUNT(*) as count FROM bets WHERE bettor_id = ?', (bettor_id,))
        bets_count = cursor.fetchone()['count']
        
        if bets_count > 0:
            keyboard = [
                [
                    InlineKeyboardButton("⚠️ Всё равно удалить", callback_data=f"force_delete_bettor_{bettor_id}"),
                    InlineKeyboardButton("❌ Отмена", callback_data="cancel_delete_bettor")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"⚠️ *У беттора {bettor['full_name']} есть ставки!*\n\n"
                f"📊 Всего ставок: *{bets_count}*\n\n"
                f"При удалении беттора ВСЕ его ставки будут удалены!\n"
                f"Вы уверены?",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            conn.close()
            return
        
        cursor.execute('DELETE FROM bettors WHERE id = ?', (bettor_id,))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            f"✅ Беттор *{bettor['full_name']}* удален!",
            parse_mode='Markdown'
        )
        
    except ValueError:
        await update.message.reply_text("❌ ID должен быть числом!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    
    finally:
        keyboard = [[KeyboardButton("🏠 Главное меню")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)

async def delete_bettor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка подтверждения удаления беттора"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("force_delete_bettor_"):
        bettor_id = int(query.data.split('_')[-1])
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT full_name FROM bettors WHERE id = ?', (bettor_id,))
        bettor = cursor.fetchone()
        bettor_name = bettor['full_name'] if bettor else f"ID {bettor_id}"
        
        cursor.execute('DELETE FROM bets WHERE bettor_id = ?', (bettor_id,))
        deleted_bets = cursor.rowcount
        
        cursor.execute('DELETE FROM bettors WHERE id = ?', (bettor_id,))
        
        conn.commit()
        conn.close()
        
        await query.edit_message_text(
            f"✅ *Беттор {bettor_name} удален!*\n"
            f"🗑 Удалено ставок: *{deleted_bets}*",
            parse_mode='Markdown'
        )
        
    elif query.data == "cancel_delete_bettor":
        await query.edit_message_text("❌ Удаление отменено")
    
    keyboard = [[KeyboardButton("🏠 Главное меню")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await query.message.reply_text("👇 Нажмите кнопку для возврата", reply_markup=reply_markup)

def format_bet_summary(data):
    """Форматирует данные ставки для красивого вывода"""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT full_name FROM bettors WHERE id = ?', (data['bettor_id'],))
    bettor = cursor.fetchone()
    
    cursor.execute('SELECT name FROM sports WHERE id = ?', (data['sport_id'],))
    sport = cursor.fetchone()
    
    cursor.execute('SELECT name FROM bet_types WHERE id = ?', (data['bet_type_id'],))
    bet_type = cursor.fetchone()
    
    conn.close()
    
    text = (
        f"📋 *ПРОВЕРЬТЕ СТАВКУ:*\n\n"
        f"👤 *Беттор:* {bettor['full_name'] if bettor else 'Неизвестно'}\n"
        f"🏆 *Вид спорта:* {sport['name'] if sport else 'Неизвестно'}\n"
        f"🎯 *Тип ставки:* {bet_type['name'] if bet_type else 'Неизвестно'}\n"
        f"📝 *Событие:* {data['event_name']}\n"
        f"📊 *Выбор:* {data['selection']}\n"
        f"💰 *Коэффициент:* {data['odds']}\n"
        f"💵 *Сумма:* {data['stake']} BYN\n"
        f"📌 *Статус:* ожидание"
    )
    
    return text