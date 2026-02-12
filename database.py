import sqlite3
from datetime import datetime
import pandas as pd
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
import os

# Имя файла базы данных
DB_NAME = 'sport_bets.db'

def get_connection():
    """Создает соединение с БД"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Чтобы можно было обращаться по именам полей
    return conn

def create_tables():
    """Создает все таблицы, если их нет"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица бетторов (люди)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bettors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL UNIQUE,
            telegram_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица видов спорта
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Таблица типов ставок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bet_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Таблица ставок (главная) - БЕЗ ДАТЫ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bettor_id INTEGER NOT NULL,
            sport_id INTEGER NOT NULL,
            bet_type_id INTEGER NOT NULL,
            event_name TEXT NOT NULL,
            selection TEXT NOT NULL,
            odds REAL NOT NULL,
            stake REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'ожидание',
            profit REAL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bettor_id) REFERENCES bettors (id),
            FOREIGN KEY (sport_id) REFERENCES sports (id),
            FOREIGN KEY (bet_type_id) REFERENCES bet_types (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Таблицы созданы (или уже существовали)")

def fill_constants():
    """Заполняет справочники начальными данными"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Добавляем виды спорта
    sports = ['Футбол', 'Хоккей', 'Теннис', 'Дота 2', 'Формула 1']
    for sport in sports:
        cursor.execute('INSERT OR IGNORE INTO sports (name) VALUES (?)', (sport,))
    
    # Добавляем типы ставок
    bet_types = ['Исход', 'Тотал', 'Фора', 'Точный счет', 'Другой']
    for bet_type in bet_types:
        cursor.execute('INSERT OR IGNORE INTO bet_types (name) VALUES (?)', (bet_type,))
    
    conn.commit()
    conn.close()
    
    print("✅ Справочники заполнены")

def init_database():
    """Инициализация всей базы"""
    create_tables()
    fill_constants()

def export_to_excel():
    """Экспортирует все данные в Excel файл"""
    
    # Создаём имя файла с датой
    filename = f"bets_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    conn = get_connection()
    
    # --- 1. БЕТТОРЫ ---
    bettors_df = pd.read_sql_query("SELECT * FROM bettors", conn)
    
    # --- 2. ВИДЫ СПОРТА ---
    sports_df = pd.read_sql_query("SELECT * FROM sports", conn)
    
    # --- 3. ТИПЫ СТАВОК ---
    bet_types_df = pd.read_sql_query("SELECT * FROM bet_types", conn)
    
    # --- 4. СТАВКИ (с расшифровкой) ---
    bets_df = pd.read_sql_query('''
        SELECT 
            b.id,
            bettors.full_name as беттор,
            sports.name as вид_спорта,
            bet_types.name as тип_ставки,
            b.event_name as событие,
            b.selection as выбор,
            b.odds as коэффициент,
            b.stake as сумма,
            b.status as статус,
                                b.profit as прибыль,
            b.created_at as дата_создания,
            b.updated_at as дата_расчета
        FROM bets b
        JOIN bettors ON b.bettor_id = bettors.id
        JOIN sports ON b.sport_id = sports.id
        JOIN bet_types ON b.bet_type_id = bet_types.id
        ORDER BY b.created_at DESC
    ''', conn)
    
    conn.close()
    
    # Создаём Excel файл с несколькими листами
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Лист со ставками
        bets_df.to_excel(writer, sheet_name='Ставки', index=False)
        
        # Лист со справочниками
        bettors_df.to_excel(writer, sheet_name='Бетторы', index=False)
        sports_df.to_excel(writer, sheet_name='Виды спорта', index=False)
        bet_types_df.to_excel(writer, sheet_name='Типы ставок', index=False)
        
        # Форматирование
        workbook = writer.book
        
        # Форматируем лист со ставками
        worksheet = writer.sheets['Ставки']
        
        # Заголовки жирным и цветом
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            cell.font = Font(bold=True, color='FFFFFF')
            cell.alignment = Alignment(horizontal='center')
        
        # Автоширина колонок
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Формат для чисел
        for row in worksheet.iter_rows(min_row=2):
            for cell in row:
                if cell.column_letter in ['G', 'H', 'J']:  # коэффициент, сумма, прибыль
                    cell.number_format = '#,##0.00'
                if cell.column_letter in ['K', 'L']:  # даты
                    cell.number_format = 'DD.MM.YYYY HH:MM'
        
        # Форматируем лист с бетторами
        worksheet = writer.sheets['Бетторы']
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            cell.font = Font(bold=True, color='FFFFFF')
        
        # Форматируем лист с видами спорта
        worksheet = writer.sheets['Виды спорта']
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            cell.font = Font(bold=True, color='FFFFFF')
        
        # Форматируем лист с типами ставок
        worksheet = writer.sheets['Типы ставок']
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            cell.font = Font(bold=True, color='FFFFFF')
    
    return filename

def import_from_excel(file_path):
    """Импортирует ставки из Excel файла"""
    
    try:
        # Читаем Excel файл
        bets_df = pd.read_excel(file_path, sheet_name='Ставки')
        
        conn = get_connection()
        cursor = conn.cursor()
        
        imported = 0
        errors = 0
        
        for _, row in bets_df.iterrows():
            try:
                # Проверяем обязательные поля
                if pd.isna(row['беттор']) or pd.isna(row['вид_спорта']) or pd.isna(row['тип_ставки']):
                    errors += 1
                    continue
                # Ищем беттора
                cursor.execute('SELECT id FROM bettors WHERE full_name = ?', (row['беттор'],))
                bettor = cursor.fetchone()
                if not bettor:
                    cursor.execute('INSERT INTO bettors (full_name) VALUES (?)', (row['беттор'],))
                    bettor_id = cursor.lastrowid
                else:
                    bettor_id = bettor['id']
                
                # Ищем вид спорта
                cursor.execute('SELECT id FROM sports WHERE name = ?', (row['вид_спорта'],))
                sport = cursor.fetchone()
                if not sport:
                    cursor.execute('INSERT INTO sports (name) VALUES (?)', (row['вид_спорта'],))
                    sport_id = cursor.lastrowid
                else:
                    sport_id = sport['id']
                
                # Ищем тип ставки
                cursor.execute('SELECT id FROM bet_types WHERE name = ?', (row['тип_ставки'],))
                bet_type = cursor.fetchone()
                if not bet_type:
                    cursor.execute('INSERT INTO bet_types (name) VALUES (?)', (row['тип_ставки'],))
                    bet_type_id = cursor.lastrowid
                else:
                    bet_type_id = bet_type['id']
                
                # Проверяем статус
                status = row['статус'] if not pd.isna(row['статус']) else 'ожидание'
                if status not in ['ожидание', 'выигрыш', 'проигрыш', 'возврат']:
                    status = 'ожидание'
                
                # Проверяем прибыль
                profit = row['прибыль'] if not pd.isna(row['прибыль']) else 0
                
                # Проверяем даты
                created_at = row['дата_создания'] if not pd.isna(row['дата_создания']) else datetime.now()
                updated_at = row['дата_расчета'] if not pd.isna(row['дата_расчета']) else created_at
                
                # Добавляем ставку
                cursor.execute('''
                    INSERT INTO bets 
                    (bettor_id, sport_id, bet_type_id, event_name, selection, 
                     odds, stake, status, profit, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    bettor_id,
                    sport_id,
                    bet_type_id,
                    row['событие'],
                    row['выбор'],
                    row['коэффициент'],
                    row['сумма'],
                    status,
                    profit,
                    created_at,
                    updated_at
                ))
                
                imported += 1
                
            except Exception as e:
                errors += 1
                print(f"Ошибка импорта строки: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return imported, errors
        
    except Exception as e:
        raise Exception(f"Ошибка чтения файла: {e}")

def create_template():
    """Создает шаблон Excel для импорта"""
    
    filename = "import_template.xlsx"
    
    # Создаем структуру для импорта
    data = {
        'беттор': ['Иван Петров'],
        'вид_спорта': ['Футбол'],
        'тип_ставки': ['Исход'],
        'событие': ['Реал - Барселона'],
        'выбор': ['П1'],
        'коэффициент': [1.85],
        'сумма': [1000],
        'статус': ['ожидание'],
        'прибыль': [0],
        'дата_создания': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        'дата_расчета': [None]
    }
    
    df = pd.DataFrame(data)
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Ставки', index=False)
        
        # Форматирование
        workbook = writer.book
        worksheet = writer.sheets['Ставки']
        
        # Заголовки
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            cell.font = Font(bold=True, color='FFFFFF')
            cell.alignment = Alignment(horizontal='center')
        
        # Автоширина
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Добавляем лист с инструкцией
        instruction_data = {
            'Поле': ['беттор', 'вид_спорта', 'тип_ставки', 'событие', 'выбор', 
                    'коэффициент', 'сумма', 'статус', 'прибыль', 'дата_создания', 'дата_расчета'],
            'Описание': [
                'Имя и фамилия беттора (будет создан автоматически)',
                'Вид спорта (будет создан автоматически)',
                'Тип ставки (будет создан автоматически)',
                'Название события/матча',
                'Ваш выбор (П1, ТБ 2.5, и т.д.)',
                'Коэффициент (число, например: 1.85)',
                'Сумма ставки (число)',
                'ожидание / выигрыш / проигрыш / возврат',
                'Прибыль (вычисляется автоматически, можно оставить 0)',
                'Дата создания ставки (формат: ГГГГ-ММ-ДД ЧЧ:ММ:СС)',
                'Дата расчета (оставьте пустым для новых ставок)'
            ],
            'Пример': [
                'Антон Петров',
                'Футбол',
                'Исход',
                'Реал - Барселона',
                'П1',
                '1.85',
                '1000',
                'ожидание',
                '0',
                '2026-02-12 19:30:00',
                ''
            ]
        }
        
        instruction_df = pd.DataFrame(instruction_data)
        instruction_df.to_excel(writer, sheet_name='Инструкция', index=False)
        
        # Форматируем инструкцию
        worksheet = writer.sheets['Инструкция']
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            cell.font = Font(bold=True, color='FFFFFF')
    
    return filename

def get_db_stats():
    """Возвращает статистику по базе данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM bets")
    total_bets = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM bets WHERE status = 'ожидание'")
    pending_bets = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM bettors")
    total_bettors = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(profit) as total FROM bets WHERE status != 'ожидание'")
    total_profit = cursor.fetchone()['total']
    if total_profit is None:
        total_profit = 0
    
    conn.close()
    
    return {
        'total_bets': total_bets,
        'pending_bets': pending_bets,
        'total_bettors': total_bettors,
        'total_profit': total_profit
    }

if __name__ == "__main__":
    init_database()
    print("✅ База данных готова к работе!")
    stats = get_db_stats()
    print(f"📊 Статистика: {stats['total_bets']} ставок, {stats['total_bettors']} бетторов")