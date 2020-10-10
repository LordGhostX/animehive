import json
import datetime
import threading
from multiprocessing import Pool
import pymongo
import telegram
from bson.objectid import ObjectId
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from extras import *

config = json.load(open("config.json"))
bot = telegram.Bot(token=config["token"])
updater = Updater(token=config["token"], use_context=True)
dispatcher = updater.dispatcher
client = pymongo.MongoClient(config["db"]["host"], config["db"]["port"])
db = client[config["db"]["db_name"]]


def launch_broadcast(args):
    try:
        bot.send_message(chat_id=args[0], text=args[1])
    except:
        pass


def echo_thread(update, context):
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
                    "Get Recommendations 🚀", callback_data="r=" + anime["session"])]]
                context.bot.send_photo(chat_id=chat_id, photo=anime["poster"], caption=config["messages"]["recommendation_search"].format(
                    anime["title"], anime["type"], anime["status"], "{} {}".format(anime["season"], anime["year"])), reply_markup=InlineKeyboardMarkup(markup))
    elif last_command == "download":
        title = update.message.text.strip()
        anime_list = search_gogoanime(title)
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
                    markup = [[InlineKeyboardButton(
                        "Get Episodes 🚀", callback_data="d=" + anime["href"])]]
                    context.bot.send_photo(
                        chat_id=chat_id, caption=f"{anime['title']}\n{anime['released']}", photo=anime["image"], reply_markup=InlineKeyboardMarkup(markup))
                except:
                    pass
    elif last_command == "get_info":
        title = update.message.text.strip()
        anime_list = search_animepahe(title)
        if len(anime_list) == 0:
            context.bot.send_message(
                chat_id=chat_id, text=config["messages"]["empty_search"])
            context.bot.send_message(
                chat_id=chat_id, text=config["messages"]["menu"])
        else:
            for anime in anime_list:
                markup = [[InlineKeyboardButton(
                    "Get Anime Info ℹ️", callback_data="i=" + anime["session"])]]
                context.bot.send_photo(chat_id=chat_id, photo=anime["poster"], caption=config["messages"]["recommendation_result"].format(
                    anime["title"], anime["status"], "{} {}".format(anime["season"], anime["year"])), reply_markup=InlineKeyboardMarkup(markup))
    elif last_command == "broadcast":
        if bot_user.get("admin"):
            message = update.message.text
            users = [[i["chat_id"], message] for i in db.users.find({})]
            with Pool(5) as p:
                result = p.map(launch_broadcast, users)
            bot.send_message(
                chat_id=chat_id, text="Finished sending broadcast message to users")
    else:
        if bot_user.get("admin"):
            context.bot.send_message(chat_id=chat_id, text=update.message.text)
        context.bot.send_message(
            chat_id=chat_id, text=config["messages"]["unknown"])
    db.users.update_one({"chat_id": chat_id}, {"$set": {"last_command": None}})


def button_thread(update, context):
    chat_id = update.effective_chat.id
    query_data = update.callback_query.data
    if query_data.split("=")[0] == "r":
        try:
            title, recommendations = fetch_animepahe_recommendations(
                query_data.split("=")[1])
            if len(recommendations) == 0:
                context.bot.send_message(
                    chat_id=chat_id, text=config["messages"]["empty_recommendation"])
            else:
                db.recommendations.insert_many([{"chat_id": chat_id, "anime": query_data.split("=")[
                                               1], "session": i["session"], "date": datetime.datetime.now()} for i in recommendations])
                context.bot.send_message(
                    chat_id=chat_id, text="Showing recommendations for {} 😇".format(title))
                for i in recommendations:
                    markup = [[InlineKeyboardButton(
                        "Get Anime Info ℹ️", callback_data="i=" + i["session"])]]
                    context.bot.send_photo(chat_id=chat_id, photo=i["image"], caption=config["messages"]["recommendation_result"].format(
                        i["title"], i["status"], i["season"]), reply_markup=InlineKeyboardMarkup(markup))
        except:
            context.bot.send_message(
                chat_id=chat_id, text=config["messages"]["empty_recommendation"])
    if query_data.split("=")[0] == "d":
        href = "https://animeout.xyz/" + \
            db.shortened_urls.find_one(
                {"_id": ObjectId(query_data.split("=")[1])})["href"]
        episodes = fetch_animeout_episodes(href)
        context.bot.send_message(
            chat_id=chat_id, text=config["messages"]["download_pagination"].format(len(episodes)))
        for i in range(0, len(episodes), 15):
            markup = [[InlineKeyboardButton(
                "Get Episodes 🚀", callback_data="f={}={}".format(query_data.split("=")[1], i))]]
            context.bot.send_message(
                chat_id=chat_id, text="Download Episodes {} - {}".format(i + 1, min(i + 15, len(episodes))), reply_markup=InlineKeyboardMarkup(markup))
    if query_data.split("=")[0] == "f":
        href = "https://animeout.xyz/" + \
            db.shortened_urls.find_one(
                {"_id": ObjectId(query_data.split("=")[1])})["href"]
        episodes = fetch_animeout_episodes(href)
        start = int(query_data.split("=")[-1])
        for i in episodes[start:start + 15]:
            try:
                download_url = db.anime.find_one({"href": i})
                if download_url:
                    download_url = download_url["download_url"]
                else:
                    download_url = fetch_animeout_download(i)
                    db.anime.insert_one({
                        "href": i,
                        "download_url": download_url,
                        "date": datetime.datetime.now()
                    })
                markup = [[InlineKeyboardButton(
                    "Download Episode 🔥", url=download_url)]]
                context.bot.send_message(
                    chat_id=chat_id, text=download_url, reply_markup=InlineKeyboardMarkup(markup))
            except:
                pass
    if query_data.split("=")[0] == "i":
        db.info.insert_one({"chat_id": chat_id, "anime": query_data.split("=")[
                           1], "date": datetime.datetime.now()})
        anime_info = fetch_animepahe_info(query_data.split("=")[1])
        markup = [[InlineKeyboardButton(
            "Get Recommendations 🚀", callback_data="r=" + query_data.split("=")[1])]]
        context.bot.send_photo(chat_id=chat_id, photo=anime_info["poster"])
        context.bot.send_message(chat_id=chat_id, text=config["messages"]["anime_info"].format(
            *list(anime_info.values())[1:-1] + [", ".join(anime_info["genre"])]), reply_markup=InlineKeyboardMarkup(markup))


def start(update, context):
    chat_id = update.effective_chat.id
    first_name = update["message"]["chat"]["first_name"]
    if not db.users.find_one({"chat_id": chat_id}):
        db.users.insert_one(
            {"chat_id": chat_id, "last_command": None, "admin": False, "date": datetime.datetime.now()})
    context.bot.send_message(
        chat_id=chat_id, text=config["messages"]["start"].format(first_name))
    context.bot.send_message(chat_id=chat_id, text=config["messages"]["menu"])
    db.users.update_one({"chat_id": chat_id}, {"$set": {"last_command": None}})


def donate(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(
        chat_id=chat_id, text=config["messages"]["donate"])
    context.bot.send_message(chat_id=chat_id, text=config["messages"]["menu"])
    db.users.update_one({"chat_id": chat_id}, {"$set": {"last_command": None}})


def help(update, context):
    chat_id = update.effective_chat.id
    total_users = db.users.count_documents({})
    total_downloaded = db.anime.count_documents({})
    total_recommendations = db.recommendations.count_documents({})
    total_info = db.info.count_documents({})
    context.bot.send_message(
        chat_id=chat_id, text=config["messages"]["help"].format(total_users, total_downloaded, total_recommendations, total_info))
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


def get_info(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(
        chat_id=chat_id, text=config["messages"]["get_info"])
    db.users.update_one({"chat_id": chat_id}, {
                        "$set": {"last_command": "get_info"}})


def broadcast(update, context):
    chat_id = update.effective_chat.id
    if db.users.find_one({"chat_id": chat_id}).get("admin"):
        num_users = db.users.count_documents({})
        context.bot.send_message(
            chat_id=chat_id, text=config["messages"]["broadcast"].format(num_users))
        db.users.update_one({"chat_id": chat_id}, {
                            "$set": {"last_command": "broadcast"}})


def echo(update, context):
    thread = threading.Thread(target=echo_thread, args=[update, context])
    thread.start()


def button(update, context):
    thread = threading.Thread(target=button_thread, args=[update, context])
    thread.start()


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
get_info_handler = CommandHandler("info", get_info)
dispatcher.add_handler(get_info_handler)
broadcast_handler = CommandHandler("broadcast", broadcast)
dispatcher.add_handler(broadcast_handler)
echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)
button_handler = CallbackQueryHandler(button)
dispatcher.add_handler(button_handler)

updater.start_polling()
