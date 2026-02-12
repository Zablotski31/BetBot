from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes


class BetBot:
    def __init__(self) -> None:
        pass

    @classmethod
    async def start(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await cls.menu_command(update, context)

    @staticmethod
    async def menu_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [KeyboardButton("🎯 Добавить ставку")],
            [KeyboardButton("📊 Активные ставки"), KeyboardButton("📜 История")],
            [KeyboardButton("👤 Бетторы"), KeyboardButton("📈 Статистика")],
            [KeyboardButton("❌ Удалить беттора"), KeyboardButton("🗑 Удалить ставку")],
            [KeyboardButton("📤 Экспорт Excel"), KeyboardButton("📥 Импорт Excel")],
            [KeyboardButton("❓ Помощь")],
        ]

        reply_markup = ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=False
        )

        await update.message.reply_text(
            "👋 *Главное меню*\n\nВыберите действие:",
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )

    @staticmethod
    async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
        """Справка с кнопкой меню"""

        keyboard = [[KeyboardButton("🏠 Главное меню")]]
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
            reply_markup=reply_markup,
        )
