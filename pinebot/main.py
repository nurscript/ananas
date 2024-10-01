from service import *
import telebot
from telebot import types
import firebase_admin
from firebase_admin import credentials, firestore, storage



if __name__ =="__main__":
    
    
    cred = credentials.Certificate("devilstore-95042-firebase-adminsdk-42e0j-f98e9de63c.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'devilstore-95042.appspot.com'
    })

    # Connect to Firestore
    db = firestore.client()
    bucket = storage.bucket()

    service = BotService(db, bucket)
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
    
    @bot.message_handler(func=lambda message: service.user_state.get(message.chat.id) == STATE_WAITING_FOR_XID)
    def handle_xid(message: types.Message):
        service.handle_xid(message) 

    @bot.message_handler(func=lambda message: service.user_state.get(message.chat.id) == STATE_WAITING_FOR_NAME)
    def handle_name(message: types.Message):
        service.handle_name(message) 

    @bot.message_handler(func=lambda message: service.user_state.get(message.chat.id) == STATE_WAITING_FOR_PRICE)
    def handle_name(message: types.Message):
        service.handle_price(message) 

    @bot.message_handler(func=lambda message: service.user_state.get(message.chat.id) == STATE_WAITING_FOR_PHOTO, content_types=['text', 'photo'])
    def handle_photo_check(message: types.Message):
        service.handle_photo_check(message) 


    @bot.callback_query_handler(func=service.replenish_methods())
    def callback_query(call: types.CallbackQuery):
        service.chosen_method(call)
    
    
    @bot.message_handler(func=lambda message: True)
    def handle_unknown(message):
        service.bot.send_message(message.chat.id, "Unknown command. Please type 'payment' to start the process.")

    bot.infinity_polling()

