from telebot import types
from app import App
from utils import flood_guard
import requests
from pathlib import Path
from collections import defaultdict
import firebase_admin
from firebase_admin import credentials, firestore, storage
import os
from datetime import datetime
from dataclasses import dataclass, asdict

# Define the different states using powers of 2
STATE_WAITING_FOR_NAME = 1 << 0  # 0001
STATE_WAITING_FOR_XID = 1 << 1   # 0010
STATE_WAITING_FOR_PRICE = 1 << 2 # 0100
STATE_WAITING_FOR_PHONE = 1 << 3 # 1000
STATE_WAITING_FOR_PHOTO = 1 << 4 # 10000

WITHDRAW_STATE = 1 << 5          # 100000
PAYMENT_STATE = 1 << 6           # 1000000
INSTRUCTION_STATE = 1 << 7 

BANK_MBANK = 1 << 0
BANK_OPTIMA = 1 << 1
BANK_ELCART = 1 << 2
BANK_CRYPTO = 1 << 3
BANK_ODENGI = 1 << 4

BANK_MASK = (
    BANK_MBANK | BANK_OPTIMA | BANK_ELCART | BANK_CRYPTO | BANK_ODENGI
)


FIELD_XID =  "xid"
FIELD_BANK = "bank"
FIELD_NAME = "name"
FIELD_PHOTO = "photo"
FIELD_PRICE = "price"
FIELD_PAID = "ever_paid"
FIELD_TIMER = "bomb_timer"

GUARD_TIME = 2 # prevent flood for 2 seconds

@dataclass
class PaymentDTO:
    user_id: int
    name: str 
    bank: str
    xid: str
    time: datetime
    photo: str
    price: int
    ever_paid: bool = False


    
class BotService(App):
    def __init__(self, lang="ru") -> None:
        super().__init__(lang)
        self._cred = credentials.Certificate("devilstore-95042-firebase-adminsdk-42e0j-f98e9de63c.json")
        firebase_admin.initialize_app(self._cred, {
            'storageBucket': 'devilstore-95042.appspot.com'
        })
        ## fire store db
        self._db = firestore.client()
        self._bucket = storage.bucket() 
        # Store user states and data
        self._user_states = defaultdict(dict)
        self._user_data = defaultdict(dict)
        volume = "checks"
        os.makedirs(volume, exist_ok=True)
        self.checks_path = Path("checks")

    def home(self, message: types.Message):
        chat_id = message.chat.id
        self._clean(chat_id)
        markup = types.ReplyKeyboardMarkup(row_width=2)
        collection = []
        for val in self.cfg.get("start_buttons"):
            btn = types.KeyboardButton(val)
            collection.append(btn)
        markup.add(*collection)
        
        msg = self.cfg.get("start").format(name=message.chat.first_name,
                                    last_name=message.chat.last_name)
        
        self.bot.send_message(chat_id, msg, reply_markup=markup)
    
    @flood_guard(GUARD_TIME)
    def choose_payment(self, message: types.Message):
        chat_id = message.chat.id
        inline_markup = types.InlineKeyboardMarkup(row_width=1)
        replenish_otions = []
        for i,val in enumerate(self.cfg.get('replenish_buttons')):
            btn = types.InlineKeyboardButton(val, callback_data=str(i | PAYMENT_STATE))
            replenish_otions.append(btn)
        inline_markup.add(*replenish_otions)

        markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
        markup.add(types.KeyboardButton(self.cfg.get('cancel')))
        text = self.cfg.get('replenish_message')
        self.bot.send_message(chat_id, '📥',reply_markup=markup)
        self.bot.send_message(chat_id, text, reply_markup=inline_markup)

    @flood_guard(GUARD_TIME)
    def choose_withdraw(self, message: types.Message):
        chat_id = message.chat.id
        inline_markup = types.InlineKeyboardMarkup(row_width=1)
        withdraw_options = []
        for i, val in enumerate(self.cfg.get('withdraw_buttons')):
            btn = types.InlineKeyboardButton(val, callback_data=str(i | WITHDRAW_STATE))
            withdraw_options.append(btn)
        inline_markup.add(*withdraw_options)
    
        markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
        markup.add(types.KeyboardButton(self.cfg.get('cancel')))
        text = self.cfg.get('withdraw_message')
        self.bot.send_message(chat_id, '📤',reply_markup=markup)
        self.bot.send_message(chat_id, text, reply_markup=inline_markup)
    

    def flood_message(self, message: types.Message):
        message.te
        self.bot.reply_to(message, self.cfg.get('flood_message'))

    def payment_option(self, option):
        option_ru = self.options['ru'].get("start_buttons")[option]
        option_ky = self.options['ky'].get("start_buttons")[option]
        return lambda message: message.text in (option_ru, option_ky)
    
    def cancel_option(self):
        option_ru = self.options['ru'].get("cancel")
        option_ky = self.options['ky'].get("cancel")
        return lambda message: message.text in (option_ru, option_ky)
    
    def state(self, flag):
        return lambda message: self._user_states.get(message.chat.id) == flag

    def chosen_method(self, call: types.CallbackQuery):
        bank_index = int(call.data) & BANK_MASK
        bank = self.cfg.get("replenish_buttons")[bank_index]
        text = self.cfg.get("chosen_method").format(method=bank)
        chat_id = call.message.chat.id
        self._user_data[chat_id][FIELD_BANK] = bank
        self._user_states[chat_id] = STATE_WAITING_FOR_NAME | PAYMENT_STATE
        self.bot.edit_message_text(text, call.message.chat.id, call.message.id)
        self.bot.answer_callback_query(call.id, text, show_alert=False)
    
    def withdraw_option(self, call: types.CallbackQuery):
        bank_index = int(call.data) & BANK_MASK
        bank = self.cfg.get("withdraw_buttons")[bank_index]
        text = self.cfg.get("withdraw_option").format(bank=bank)
        chat_id = call.message.chat.id
        self._user_data[chat_id][FIELD_BANK] = bank
        self._user_states[chat_id] = STATE_WAITING_FOR_XID | WITHDRAW_STATE
        self.bot.edit_message_text(text, call.message.chat.id, call.message.id)
        self.bot.answer_callback_query(call.id, text, show_alert=False)
        self.bot.send_message(chat_id, self.cfg.get('withdraw_request_bank_id'))

    
    def handle_name(self, message: types.Message):
        chat_id = message.chat.id
        self._user_data[chat_id][FIELD_NAME] = message.text
        self._user_states[chat_id] = STATE_WAITING_FOR_XID | PAYMENT_STATE

        markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
        if self._user_data[chat_id].get(FIELD_XID):
          markup.add(types.KeyboardButton(self._user_data[chat_id].get(FIELD_XID)))
        markup.add(types.KeyboardButton(self.cfg.get('cancel')))
        self.bot.send_message(chat_id, self.cfg.get("handle_xid"), reply_markup=markup)
    
    def handle_xid(self, message: types.Message):
        chat_id = message.chat.id
        # identify the xid
        msg: str = message.text
        if not (msg.isnumeric() and 14 >=len(msg) >=9):
            self.bot.send_message(chat_id, self.cfg.get("invalid_xid"))
            return
        self._user_data[chat_id][FIELD_XID] = msg
        self._user_states[chat_id] = STATE_WAITING_FOR_PRICE | PAYMENT_STATE

        # add price keyboard
        markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
        if self._user_data[chat_id].get(FIELD_PRICE):
            markup.add(types.KeyboardButton(self._user_data[chat_id].get(FIELD_PRICE)))
        markup.add(types.KeyboardButton(self.cfg.get('cancel')))
        # move to next state
        self.bot.send_message(chat_id, self.cfg.get("handle_price"), reply_markup=markup)
    
    def handle_xid_withdraw(self, message: types.Message):
        chat_id = message.chat.id
        # identify the xid
        msg: str = message.text
        if not (msg.isnumeric() and 14 >=len(msg) >=9):
            self.bot.send_message(chat_id, self.cfg.get("invalid_xid"))
            return
        self._user_data[chat_id][FIELD_XID] = msg
        self._user_states[chat_id] = STATE_WAITING_FOR_PRICE | WITHDRAW_STATE
        if not self._user_data[chat_id].get(FIELD_PAID):
            self.bot.send_message(chat_id, self.cfg.get('withdraw_conditions'))
            return
        
        text = self.cfg.get("handle_price")
        # move to next state
        self.bot.send_message(chat_id, text)
    

    def handle_price(self, message: types.Message, process_state: int):
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
        if process_state == WITHDRAW_STATE:
            text = self.cfg.get('report_withdraw').format(
                name=self._user_data[chat_id][FIELD_NAME],
                bank=self._user_data[chat_id][FIELD_BANK],
                xid=self._user_data[chat_id][FIELD_XID],
                price=self._user_data[chat_id][FIELD_PRICE]
            )
            self._user_states[chat_id] = 0
            self.bot.send_message(chat_id,text)
            return
        
        markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
        markup.add(types.KeyboardButton(self.cfg.get('cancel')))
            
        self._user_states[chat_id] = STATE_WAITING_FOR_PHOTO | process_state
        self.bot.send_message(chat_id, self.cfg.get("pay_info").format(price=price), reply_markup=markup)
    
    def handle_photo_check(self, message: types.Message):
        chat_id = message.chat.id
        # identify the type of message 
        print(message.content_type)
        if message.content_type != "photo":
            self.bot.send_message(chat_id, "only photo is allowed")
            return
        
        file_info = self.bot.get_file(message.photo[-1].file_id)
        downloaded_file = self.bot.download_file(file_info.file_path)
        photo_path = self.checks_path / f"{chat_id}_check.jpg"
        with open(photo_path, 'wb') as f:
            f.write(downloaded_file)
        

        self._user_data[chat_id][FIELD_PHOTO] = photo_path
        date_time = datetime.now()
        stamp = date_time.strftime("%m%d%y%H%M%S")
        image_url = self._upload_check_image(photo_path, f"payments/{stamp}_{os.path.basename(photo_path)}")

        dto = PaymentDTO(
            chat_id,
            self._user_data[chat_id][FIELD_NAME],
            self._user_data[chat_id][FIELD_BANK],
            self._user_data[chat_id][FIELD_XID],
            datetime.now(),
            image_url,
            self._user_data[chat_id][FIELD_PRICE]
        )

        self._add_user_data(dto)
        markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
        markup.add(types.KeyboardButton(self.cfg.get('cancel')))
        self.bot.send_message(chat_id, self.cfg.get("report_payment").format(
            name=dto.name,
            bank=dto.bank,
            xid=dto.xid,
            price=dto.price
        ), reply_markup=markup)
        # if pay transaction is passed
        self._user_data[chat_id][FIELD_PAID] = True
        self._clean(chat_id)
    
    def _clean(self,chat_id):
        if self._user_states.get(chat_id):
            self._user_states[chat_id] = 0
    
    def _add_user_data(self, dto: PaymentDTO):
        doc_ref = self._db.collection('payment').document(str(dto.user_id))
        dt = asdict(dto)
        print(dt)
        doc_ref.set(dt)

    def on_snapshot(self, doc_snapshot, changes, read_time):
        for doc in doc_snapshot:
            print(f"received document snapshot: {doc.id}")
            
    
    def _upload_check_image(self, image_path, image_name):
        # Upload an image to Firebase Storage
        blob = self._bucket.blob(image_name)
        blob.upload_from_filename(image_path)
        # Make the image publicly accessible
        blob.make_public()
        # Get the public URL of the uploaded image
        return blob.public_url
    
    def misunderstand(self, message: types.Message):
        self.bot.send_message(message.chat.id, self.cfg.get("misunderstanding"))
    

    def instructions(self, message: types.Message):
        chat_id = message.chat.id
        inline_markup = types.InlineKeyboardMarkup(row_width=1)
        replenish_otions = []
        btns = self.cfg.get('start_buttons')
        if len(btns) < 2:
            self.bot.send_message(chat_id, self.cfg.get('oops'))
            return
        for i,val in enumerate(btns[:2]):
            btn = types.InlineKeyboardButton(val, callback_data=str(i | INSTRUCTION_STATE))
            replenish_otions.append(btn)
        inline_markup.add(*replenish_otions)
        self.bot.send_message(chat_id, self.cfg.get("instructions"), reply_markup=inline_markup)
    
    def get_tutorial(self, callback: types.CallbackQuery):
        button_index = int(callback.data) & 3
        button = self.cfg.get("start_buttons")[button_index]
        chat_id = callback.message.chat.id
        if button_index == 0:
            self.bot.send_message(chat_id,f"Tutorial: {button}")
        elif button_index == 1:
            self.bot.send_message(chat_id,f"Urok: {button}")

    def change_lang(self, message: types.Message):
        self.toggle_lang()
        self.home(message)

    

    
