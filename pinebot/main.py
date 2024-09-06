from service import BotService

import telebot
from telebot import types

if __name__ =="__main__":
    
    service = BotService()
    bot: telebot.TeleBot = service.bot

    # bot start handler
    @bot.message_handler(commands=['start'])
    def start(message: types.Message):
        service.home(message)
    # bot start handler
    @bot.message_handler(regexp="^Cancel$")
    def start(message: types.Message):
        service.home(message)

    @bot.message_handler(regexp=service.payment_option)
    def choose_payment(message: types.Message):
        service.choose_payment(message)
    
    @bot.callback_query_handler(func=service.replenish_methods())
    def callback_query(call: types.CallbackQuery):
        service.chosen_method(call)
    

    bot.infinity_polling()

