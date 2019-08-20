import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, ConversationHandler
from telegram.ext import InlineQueryHandler

from services.web import Currency, Weather, WEATHER_KEY, CURRENCY_CODES

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                     level=logging.DEBUG, filename='log.txt')

logger = logging.getLogger(__name__)


CHOOSING, WEATHER, CURRENCY = range(3)

TOKEN = "TOKEN"

REQUEST_KWARGS = {"proxy_url": "http://23.237.173.102:3128/"}


keyboard = [[InlineKeyboardButton("Weather", callback_data="weather"),
             InlineKeyboardButton("Currency", callback_data="currency")],
            ]

reply_markup = InlineKeyboardMarkup(keyboard)


def start(bot, update):

    name = update.message.chat.first_name
    update.message.reply_text("Hello {name}! I'm glad to see you! What would you like to know".format(name=name),
                              reply_markup=reply_markup)
    return CHOOSING


def inline_switch_pm(bot, update):

    results = list()
    update.inline_query.answer(results, cache_time=0, switch_pm_text='Start private chat', switch_pm_parameter='hh')


def button(bot, update):
    query = update.callback_query

    if query.data == "weather":
        response = "Please, type name of the city which you are interested in. You can send me your location as well."
        result = WEATHER
    else:
        response = "Please type the currency code to know how much it costs"
        result = CURRENCY

    bot.edit_message_text(text="Got it! {}".format(response),
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)
    return result


def get_weather(bot, update):
    text = update.message.text
    location = update.message.location
    city_weather = Weather(city_name=text,
                           location=location,
                           api_key=WEATHER_KEY,
                           url="https://api.openweathermap.org")
    weather = city_weather.current()
    if isinstance(weather, dict):
        update.message.reply_text("City: {name}\n"
                                  "Temperature: {temp} C\n"
                                  "Pressure: {pressure} mmHg\n"
                                  "Humidity: {humidity} %\n"
                                  "Wind: {wind}".format(**weather))
        return WEATHER

    elif weather:
        update.message.reply_text(weather)
        return WEATHER

    update.message.reply_text("Sorry, I didn't find any information. Please note, I understand English only.\n"
                              "Use /back to return to the main menu.")
    return WEATHER

def get_currency(bot, update):
    currency_codes = ', '.join(CURRENCY_CODES)
    code = update.message.text
    currency = Currency(url='https://api.exchangerate-api.com', currency=code)
    latest_rates = currency.latest_rates()

    if isinstance(latest_rates, dict):
        text = ''
        for key, value in latest_rates.items():
            text += '{key}: {value}\n'.format(key=key, value=value)
        update.message.reply_text(text)
        return CURRENCY

    elif latest_rates:
        update.message.reply_text(latest_rates)

        return CURRENCY

    update.message.reply_text("Sorry, I didn't find any information. Please check if yoy type currency correctly.\n"
                              "Possible codes are {codes}.\n"
                              "Use /back to return to the main menu.".format(codes=currency_codes))
    return CURRENCY


def back(bot, update):
    name = update.message.chat.first_name
    update.message.reply_text("OK, {name}! Which option would you like to choose?".format(name=name),
                              reply_markup=reply_markup)
    return CHOOSING


def help(bot, update):
    update.message.reply_text("This bot can help you with searching information about weather and currency.\n"
                              "There are the commands which are supported by the bot:\n"
                              "/help - this help.\n"
                              "/start - the beginning of the dialog with the bot.\n"
                              "/back - return to the main menu.\n"
                              "/finish - use it to stop the dialog.")


def finish(bot, update):
    user = update.message.chat.first_name
    logger.info("User {user} canceled the conversation.".format(user=user))
    update.message.reply_text("Good Bye {user}! I hope I was useful for you.\n"
                              "Use /start to begin the conversation."
                              .format(user=user))

    return ConversationHandler.END


def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning("Update '%s' caused error '%s'", update, error)


def main():
    updater = Updater(token=TOKEN, request_kwargs=REQUEST_KWARGS)
    dispatcher = updater.dispatcher

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],

        states={
            CHOOSING: [CallbackQueryHandler(button)],

            WEATHER: [MessageHandler(Filters.location | Filters.text, get_weather),
                      CommandHandler("back", back)],

            CURRENCY: [MessageHandler(Filters.text, get_currency),
                      CommandHandler("back", back)],


        },

        fallbacks=[CommandHandler("finish", finish)]
    )
    
    # handlers
    help_handler = CommandHandler("help", help)
    inline_switch_pm_handler = InlineQueryHandler(inline_switch_pm)
    unknown_handler = MessageHandler(Filters.command, unknown)

    # registration handlers
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(inline_switch_pm_handler)
    dispatcher.add_handler(unknown_handler)

    # log all errors
    dispatcher.add_error_handler(error)

    # start the bot
    updater.start_polling(timeout=5)
    # stop the bot gracefully
    updater.idle()
