from typing import Self


import sqlite3

db_connection = sqlite3.connect("sport_bets.db")
db_connection.row_factory = sqlite3.Row


class DbRepository:
    def __init__(self) -> None:
        self.connection = db_connection

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.connection.commit()
        return False

    def init_db(self) -> None:
        cursor = self.connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bettors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL UNIQUE,
                telegram_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bet_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        cursor.execute("""
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
        """)

        sports = ["Футбол", "Хоккей", "Теннис", "Дота 2", "Формула 1"]
        for sport in sports:
            cursor.execute("INSERT OR IGNORE INTO sports (name) VALUES (?)", (sport,))

        bet_types = ["Исход", "Тотал", "Фора", "Точный счет", "Другой"]
        for bet_type in bet_types:
            cursor.execute(
                "INSERT OR IGNORE INTO bet_types (name) VALUES (?)", (bet_type,)
            )

        print("Database is initialized")

    def get_db_stats(self):
        """Возвращает статистику по базе данных"""
        cursor = self.connection.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM bets")
        total_bets = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM bets WHERE status = 'ожидание'")
        pending_bets = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM bettors")
        total_bettors = cursor.fetchone()["count"]

        cursor.execute(
            "SELECT SUM(profit) as total FROM bets WHERE status != 'ожидание'"
        )
        total_profit = cursor.fetchone()["total"]
        if total_profit is None:
            total_profit = 0

        return {
            "total_bets": total_bets,
            "pending_bets": pending_bets,
            "total_bettors": total_bettors,
            "total_profit": total_profit,
        }

    def list_bettors(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT 
                b.id, 
                b.full_name,
                COUNT(bets.id) as bets_count
            FROM bettors b
            LEFT JOIN bets ON b.id = bets.bettor_id
            GROUP BY b.id
            ORDER BY b.full_name
        """)
        bettors = cursor.fetchall()

        return bettors
