
from telebot.types import (
    InlineKeyboardMarkup as IM, InlineKeyboardButton as IB
)

from translator import get_langs, get_lang_title

def get_langs_rm(rm: IM, user_id: int, additional="set_lang") -> IM:
    btns = []
    for lang in get_langs():
        if len(lang) <= 3:
            btns.append(IB(get_lang_title(lang), callback_data=f'set_lang:{additional}:{lang}', user_id=user_id))
    rm.add(*btns, row_width=3)
    return rm