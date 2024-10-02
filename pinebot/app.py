import os
import toml
import telebot
from typing import Tuple
# System settings level 
# Base app
settings = {
    "ru": "config_ru.toml",
    "ky": "config_ky.toml"
}

class App:
    def __init__(self, lang = "ru") -> None:
        self._lang = lang
        self._token = os.environ['TOKEN']
        self._bot = telebot.TeleBot(self._token)
        self._min_price = 3000
        self._max_price = 100000
        self._configuration = {'ru':{}, 'ky':{}}
        self._load_settings()
    
    @property
    def bot(self):
        return self._bot
    
    @property
    def cfg(self)->dict:
        return self._configuration.get(self._lang).get("bot")
    
    @property
    def options(self) ->dict:
        return {'ru':self._configuration.get('ru').get('bot'),
                'ky':self._configuration.get('ky').get('bot')
                }
    
    def _load_settings(self):
        for lang, config_file in settings.items():
            with open(config_file,  "rt") as f:
                self._configuration[lang] = toml.load(f)

    def toggle_lang(self):
        self._lang = "ky" if self._lang == "ru" else "ru"

    

        

