#  RimMirK's Telegram Bot Template - Template for building Telegram bots
#  Copyright (C) 2025-present RimMirK
#
#  This file is part of the RimMirK's Telegram Bot Template.
#
#  Telegram Bot Template is free software: you can use, modify, and redistribute
#  it under the terms of the Apache License 2.0.
#
#  Use responsibly and respect the author's work.
#
#  LICENSE: See LICENSE file for full terms.
#  NOTICE: Dear developer — this file is written especially for you.
#          Take a moment to read it: inside is a message, acknowledgements,
#          and guidance that matter.
#
#  Repository: https://github.com/RimMirK/RimMirKs_TelegramBotTemplate
#  Telegram: @RimMirK



from telebot.types import (
    InlineKeyboardMarkup as IM, InlineKeyboardButton as IB,
    CallbackQuery as C, Message, Message as M,
    CopyTextButton
)

import requests

from cpytba import CustomAsyncTeleBot as Bot
from database import DB
from translator import get_text_translations, tr
from logging import Logger
from utils import paste

async def main(bot: Bot, db: DB, logger: Logger):

    
    bot.add_command(4, ['rules'], await get_text_translations("cmd_desc.rules"))
    @bot.message_handler(['rules'])
    async def _rules(msg: Message):
        _ = await tr(msg)
        
        with open("rules/"+await _('rules_file', 'rules.ru.md'), 'r', encoding='utf-8') as f:
            url = paste(f.read(), 'md')
        
        if not await db.is_rules_confirmed(msg.from_user.id):
            rm = IM()
            rm.add(IB(await _('rules.confirm_rules_btn'), callback_data='confirm_rules', user_id=msg.from_user.id))
            
            await bot.reply(msg, await _('rules.confirm_rules_text', rules_url=url), reply_markup=rm)
        else:
            await bot.reply(msg, await _('rules.rules_text', rules_url=url))


    @bot.callback_query_handler(cs='confirm_rules')
    async def _confirm_rules(c: C):
        await db.set_rules_confirmed(c.from_user.id)
        _ = await tr(c)
        
        
        rm = IM()
        rm.add(IB(await _('start_lang.get_started'), callback_data='get_started', user_id=c.from_user.id))
        
        await bot.edit(c.message, await _('rules.rules_confirmed_text'), reply_markup=rm)