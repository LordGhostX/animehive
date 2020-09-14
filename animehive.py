import json
from telegram.ext import Updater
from telegram.ext import CommandHandler

config = json.load(open("config.json"))
updater = Updater(token=config["token"], use_context=True)
dispatcher = updater.dispatcher


def start(update, context):
    chat_id = update.effective_chat.id
    first_name = update["message"]["chat"]["first_name"]
    context.bot.send_message(
        chat_id=chat_id, text=config["messages"]["start"].format(first_name))
    context.bot.send_message(chat_id=chat_id, text=config["messages"]["menu"])


def donate(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(
        chat_id=chat_id, text=config["messages"]["donate"])


start_handler = CommandHandler("start", start)
dispatcher.add_handler(start_handler)
donate_handler = CommandHandler("donate", donate)
dispatcher.add_handler(donate_handler)

updater.start_polling()
