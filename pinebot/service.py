from telebot import types
from app import App
from utils import flood_guard
import requests
from pathlib import Path
from collections import defaultdict

# Define the different states a user can be in
STATE_WAITING_FOR_NAME = 1
STATE_WAITING_FOR_XID = 2
STATE_WAITING_FOR_PRICE = 3
STATE_WAITING_FOR_PHONE = 4
STATE_WAITING_FOR_PHOTO = 5

FIELD_XID =  "xid"
FIELD_BANK = "bank"
FIELD_NAME = "name"
FIELD_PHOTO = "photo"
FIELD_PRICE = "price"


class BotService(App):
    def __init__(self, lang="ru") -> None:
        super().__init__(lang)

        # Store user states and data
        self._user_states = defaultdict(dict)
        self._user_data = defaultdict(dict)
        self.checks_path = Path("checks")

    def home(self, message: types.Message):
        chat_id = message.chat.id
        markup = types.ReplyKeyboardMarkup(row_width=2)
        collection = []
        for val in self.cfg.get("start_buttons"):
            btn = types.KeyboardButton(val)
            collection.append(btn)
        markup.add(*collection)
        
        msg = self.cfg.get("start").format(name=message.chat.first_name,
                                    last_name=message.chat.last_name)
        
        self.bot.send_message(chat_id, msg, reply_markup=markup)
    
    @flood_guard(2)
    def choose_payment(self, message: types.Message):
        chat_id = message.chat.id
        inline_markup = types.InlineKeyboardMarkup(row_width=1)
        replenish_otions = []
        for val in self.cfg.get('replenish_buttons'):
            btn = types.InlineKeyboardButton(val, callback_data=str(val))
            replenish_otions.append(btn)
        inline_markup.add(*replenish_otions)

        markup = types.ReplyKeyboardMarkup(row_width=1)
        markup.add(types.KeyboardButton('Cancel'))
        text = self.cfg.get('replenish_message')
        self.bot.send_message(chat_id, '📥',reply_markup=markup)
        self.bot.send_message(chat_id, text, reply_markup=inline_markup)

    def flood_message(self, message: types.Message):
        self.bot.reply_to(message, self.cfg.get('flood_message'))
    
    @property
    def payment_option(self):
        option = self.cfg.get("start_buttons")[0]
        return f'^{option}$'
    
    @property
    def user_state(self) -> dict:
        return self._user_states
    
    def replenish_methods(self):
        return lambda call:  call.data in self.cfg.get("replenish_buttons")
    
    def chosen_method(self, call: types.CallbackQuery):
        text = self.cfg.get("chosen_method").format(method=call.data)
        chat_id = call.message.chat.id
        self._user_data[chat_id][FIELD_BANK] = call.data
        self._user_states[chat_id] = STATE_WAITING_FOR_NAME
        self.bot.edit_message_text(text, call.message.chat.id, call.message.id)
        self.bot.answer_callback_query(call.id, text, show_alert=False)

    def handle_name(self, message: types.Message):
        chat_id = message.chat.id
        self._user_data[chat_id][FIELD_NAME] = message.text
        self._user_states[chat_id] = STATE_WAITING_FOR_XID
        self.bot.send_message(chat_id, self.cfg.get("handle_xid"))
    
    def handle_xid(self, message: types.Message):
        chat_id = message.chat.id
        # identify the xid
        msg: str = message.text
        if not (msg.isnumeric() and 13 >=len(msg) >=9):
            self.bot.send_message(chat_id, self.cfg.get("invalid_xid"))
            return
        self._user_data[chat_id][FIELD_XID] = msg
        self._user_states[chat_id] = STATE_WAITING_FOR_PRICE
        # move to next state
        self.bot.send_message(chat_id, self.cfg.get("handle_price"))

    def handle_price(self, message: types.Message):
        chat_id = message.chat.id
        price = 0
        msg: str = message.text
        if not msg.isdecimal():
            self.bot.send_message(chat_id, self.cfg.get("invalid_price"))
            return
        price = int(msg)
        if not self._min_price<=price<=self._max_price:
            self.bot.send_message(chat_id, self.cfg.get("invalid_price"))
            return
        
        self._user_data[chat_id][FIELD_PRICE] = price
        self._user_states[chat_id] = STATE_WAITING_FOR_PHOTO
        self.bot.send_message(chat_id, self.cfg.get("check_photo"))
    
    def handle_photo_check(self, message: types.Message):
        chat_id = message.chat.id
        # identify the type of message 
        print(message.content_type)
        if message.content_type != "photo":
            self.bot.send_message(chat_id, "only photo is allowed")
            return
        
        file_info = self.bot.get_file(message.photo[0].file_id)
        downloaded_file = self.bot.download_file(file_info.file_path)
        photo_path = self.checks_path / f"{chat_id}_check.jpg"
        with open(photo_path, 'wb') as f:
            f.write(downloaded_file)

        self._user_data[chat_id][FIELD_PHOTO] = photo_path

        try:
            response = requests.post(
                'http://localhost:8000/api/payment', 
                data={'bank':self._user_data[chat_id][FIELD_BANK] ,
                      'name': self._user_data[chat_id][FIELD_NAME], 
                      'xid': self._user_data[chat_id][FIELD_XID], 
                      'price': self._user_data[chat_id][FIELD_PRICE]},
                files={'photo': open(photo_path, 'rb')}
            )
            
            if response.status_code == 200:
                self.bot.send_message(chat_id, "Your payment information has been successfully submitted. Wait for updates soon.")
            else:
                self.bot.send_message(chat_id, "There was an error submitting your information. Please try again later.")
        except Exception as e:
            self.bot.send_message(chat_id, f"Error: {e}")
        
        del self._user_states[chat_id]
        del self._user_data[chat_id]

        
    

    
    
