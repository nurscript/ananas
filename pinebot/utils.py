
import time
from telebot import types
from functools import wraps

def flood_guard(delta_time: float):
    def decorator(func):
        last_called = {}
        @wraps(func)
        def wrapper(service , message: types.Message):
            current_time = time.time()
            chat_id = message.chat.username
            if chat_id in last_called:
                elapsed_time = current_time - last_called[chat_id]
                if elapsed_time < delta_time:
                    return service.flood_message(message)
            last_called[chat_id] = current_time
            return func(service, message)
        return wrapper
    return decorator