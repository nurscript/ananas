from service import *
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
    @bot.message_handler(func=service.cancel_option())
    def start(message: types.Message):
        service.home(message)

    @bot.message_handler(func=service.payment_option(0))
    def choose_payment(message: types.Message):
        service.choose_payment(message)
    
    @bot.message_handler(func=service.payment_option(1))
    def choose_witdraw(message: types.Message):
        service.choose_withdraw(message)
    
    @bot.message_handler(func=service.payment_option(2))
    def choose_instructions(message: types.Message):
        service.instructions(message)


    @bot.message_handler(func=service.payment_option(3))
    def choose_instructions(message: types.Message):
        service.change_lang(message)    

    @bot.message_handler(func=service.state(STATE_WAITING_FOR_XID | PAYMENT_STATE))
    def handle_xid(message: types.Message):
        service.handle_xid(message) 
   
    @bot.message_handler(func=service.state(STATE_WAITING_FOR_XID | WITHDRAW_STATE))
    def handle_xid_withdraw(message: types.Message):
        service.handle_xid_withdraw(message) 

    @bot.message_handler(func=service.state(STATE_WAITING_FOR_NAME | PAYMENT_STATE))
    def handle_name(message: types.Message):
        service.handle_name(message) 

    @bot.message_handler(func=service.state(STATE_WAITING_FOR_PRICE | PAYMENT_STATE))
    def handle_name(message: types.Message):
        service.handle_price(message, PAYMENT_STATE)
    
    @bot.message_handler(func=service.state(STATE_WAITING_FOR_PRICE | WITHDRAW_STATE))
    def handle_name(message: types.Message):
        service.handle_price(message, WITHDRAW_STATE) 

    @bot.message_handler(func=service.state(STATE_WAITING_FOR_PHOTO | PAYMENT_STATE), content_types=['text', 'photo'])
    def handle_photo_check(message: types.Message):
        service.handle_photo_check(message) 


    @bot.callback_query_handler(func=lambda call:  int(call.data) & PAYMENT_STATE )
    def callback_query(call: types.CallbackQuery):
        service.chosen_method(call)
    
    
    @bot.callback_query_handler(func=lambda call:  int(call.data) & WITHDRAW_STATE )
    def callback_query_payment(call: types.CallbackQuery):
        service.withdraw_option(call)
    
    @bot.callback_query_handler(func=lambda call:  int(call.data) & INSTRUCTION_STATE )
    def callback_get_tutorial(call: types.CallbackQuery):
        service.get_tutorial(call)
    
    
    @bot.message_handler(func=lambda message: True)
    def handle_unknown(message):
        service.misunderstand(message)
    bot.infinity_polling()

