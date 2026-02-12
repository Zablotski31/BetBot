from telegram import Update
from telegram.ext import Application, CommandHandler

from my_bot import BetBot
from db_repository import DbRepository


with DbRepository() as db:
    db.init_db()


TOKEN = "8046876619:AAFxFAgUp-m1LAbH5duUOJt7Uk0jIXAj1pQ"

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", BetBot.start))
app.add_handler(CommandHandler("help", BetBot.help_command))
app.add_handler(CommandHandler("menu", BetBot.menu_command))

app.run_polling(allowed_updates=Update.ALL_TYPES)
