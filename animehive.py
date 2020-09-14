import os
import json
import datetime
import pymongo
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from extras import *

config = json.load(open("config.json"))
updater = Updater(token=config["token"], use_context=True)
dispatcher = updater.dispatcher
client = pymongo.MongoClient(config["db"]["host"], config["db"]["port"])
db = client[config["db"]["db_name"]]


def start(update, context):
    chat_id = update.effective_chat.id
    first_name = update["message"]["chat"]["first_name"]
    if not db.users.find_one({"chat_id": chat_id}):
        db.users.insert_one(
            {"chat_id": chat_id, "last_command": None, "date": datetime.datetime.now()})
    context.bot.send_message(
        chat_id=chat_id, text=config["messages"]["start"].format(first_name))
    context.bot.send_message(chat_id=chat_id, text=config["messages"]["menu"])
    db.users.update_one({"chat_id": chat_id}, {"$set": {"last_command": None}})


def donate(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(
        chat_id=chat_id, text=config["messages"]["donate"])
    db.users.update_one({"chat_id": chat_id}, {"$set": {"last_command": None}})


def help(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(
        chat_id=chat_id, text=config["messages"]["help"])
    db.users.update_one({"chat_id": chat_id}, {"$set": {"last_command": None}})


def recommend(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(
        chat_id=chat_id, text=config["messages"]["recommend"])
    db.users.update_one({"chat_id": chat_id}, {
                        "$set": {"last_command": "recommend"}})


def download(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(
        chat_id=chat_id, text=config["messages"]["download"])
    db.users.update_one({"chat_id": chat_id}, {
                        "$set": {"last_command": "download"}})


def echo(update, context):
    chat_id = update.effective_chat.id
    bot_user = db.users.find_one({"chat_id": chat_id})
    last_command = bot_user["last_command"]

    if last_command == "recommend":
        title = update.message.text.strip()
        anime_list = search_animepahe(title)
        if len(anime_list) == 0:
            context.bot.send_message(
                chat_id=chat_id, text=config["messages"]["empty_search"])
            context.bot.send_message(
                chat_id=chat_id, text=config["messages"]["menu"])
        else:
            context.bot.send_message(
                chat_id=chat_id, text="Displaying search results for {} 😁".format(title))
            for anime in anime_list:
                markup = [[InlineKeyboardButton(
                    "Get Recommendations 🚀", callback_data="r=" + str(anime["session"]))]]
                context.bot.send_message(chat_id=chat_id, text=config["messages"]["recommendation_search"].format(
                    anime["title"], anime["type"], anime["status"], "{} {}".format(anime["season"], anime["year"])), reply_markup=InlineKeyboardMarkup(markup))
    elif last_command == "download":
        title = update.message.text.strip()
        anime_list = search_animeout(title)
        if len(anime_list) == 0:
            context.bot.send_message(
                chat_id=chat_id, text=config["messages"]["empty_search"])
            context.bot.send_message(
                chat_id=chat_id, text=config["messages"]["menu"])
        else:
            context.bot.send_message(
                chat_id=chat_id, text="Displaying search results for {} 😁".format(title))
            for anime in anime_list:
                try:
                    href = anime["href"][25:-1]
                    markup = [[InlineKeyboardButton(
                        "Get Episodes 🚀", callback_data="d=" + href)]]
                    context.bot.send_photo(
                        chat_id=chat_id, caption=anime["title"], photo=anime["image"], reply_markup=InlineKeyboardMarkup(markup))
                except:
                    pass
    else:
        context.bot.send_message(
            chat_id=chat_id, text=config["messages"]["unknown"])
    db.users.update_one({"chat_id": chat_id}, {"$set": {"last_command": None}})


def button(update, context):
    chat_id = update.effective_chat.id
    query_data = update.callback_query.data
    if query_data.split("=")[0] == "r":
        title, recommendations = fetch_recommendations(
            query_data.split("=")[1])
        if len(recommendations) == 0:
            context.bot.send_message(
                chat_id=chat_id, text=config["messages"]["empty_recommendation"])
        else:
            context.bot.send_message(
                chat_id=chat_id, text="Showing recommendations for {} 😇".format(title))
            for i in recommendations:
                context.bot.send_message(chat_id=chat_id, text=config["messages"]["recommendation_result"].format(
                    i["title"], i["status"], i["season"]))
    if query_data.split("=")[0] == "d":
        href = "https://animeout.xyz/" + query_data.split("=")[1]
        episodes = fetch_episodes(href)
        for i in episodes:
            markup = [[InlineKeyboardButton("Download Episode 🔥", url=i)]]
            context.bot.send_message(chat_id=chat_id, text=os.path.basename(
                i), reply_markup=InlineKeyboardMarkup(markup))


start_handler = CommandHandler("start", start)
dispatcher.add_handler(start_handler)
donate_handler = CommandHandler("donate", donate)
dispatcher.add_handler(donate_handler)
help_handler = CommandHandler("help", help)
dispatcher.add_handler(help_handler)
recommend_handler = CommandHandler("recommend", recommend)
dispatcher.add_handler(recommend_handler)
download_handler = CommandHandler("download", download)
dispatcher.add_handler(download_handler)
echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)
button_handler = CallbackQueryHandler(button)
dispatcher.add_handler(button_handler)

updater.start_polling()
