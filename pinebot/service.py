from telebot import types
from app import App
from utils import flood_guard
class BotService(App):
    def __init__(self, lang="ru") -> None:
        super().__init__(lang)


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
    
    def replenish_methods(self):
        return lambda call:  call.data in self.cfg.get("replenish_buttons")
    
    def chosen_method(self, call: types.CallbackQuery):
        text = self.cfg.get("chosen_method").format(method=call.data)
        self.bot.edit_message_text(text, call.message.chat.id, call.message.id)
        self.bot.answer_callback_query(call.id, text, show_alert=False)

    def mbank_option(self, message:types.Message):
        pass

    def optima_option(self, message:types.Message):
        pass

    
    
