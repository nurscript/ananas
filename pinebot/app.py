import os
import tomllib
import telebot
# System settings level 
# Base app
settings = {
    "ru": "config_ru.toml",
    "ky": "config_ky.toml"
}

class App:
    def __init__(self, lang = "ru") -> None:
        self._lang = lang
        self._load_settings()
        self._token = os.environ['TOKEN']
        self._bot = telebot.TeleBot(self._token)
    
    @property
    def bot(self):
        return self._bot
    
    @property
    def cfg(self)->dict:
        return self._configuration.get("bot")
    
    # depends on self._lang
    def _load_settings(self):
        with open(settings[self._lang],  "rb") as f:
            self._configuration = tomllib.load(f)

    def toggle_lang(self):
        self._lang = "ky" if self._lang == "ru" else "ru"
        self._load_settings()

    

        

