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
    CopyTextButton, ReplyKeyboardRemove as RKR
)

from cpytba import CustomAsyncTeleBot as Bot
from database import DB
from translator import get_text_translations, tr
from logging import Logger

from utils.utils import paste

async def main(bot: Bot, db: DB, logger: Logger):

    async def flt(msg):
        return msg.text in (await get_text_translations('back.back_to_menu_btn')).values()

    bot.add_command(1, ['menu', 'get_started'], await get_text_translations("cmd_desc.menu"))
    @bot.callback_query_handler(cs='get_started')
    @bot.message_handler(['get_started', 'menu'])
    @bot.message_handler(func=flt)
    async def _get_started(obj: C|M):
        c = obj if isinstance(obj, C) else None
        m = obj if isinstance(obj, M) else c.message
        
        if isinstance(obj, M):
            lm = await bot.reply(m, 'loading...', reply_markup=RKR())
            await bot.delete(lm)

        
        _ = await tr(obj)
        
        if not await db.is_rules_confirmed(obj.from_user.id):
            
            rm = IM()
            rm.add(IB(await _('rules.confirm_rules_btn'), callback_data='confirm_rules'), user_id=obj.from_user.id)
            
            with open("rules/"+await _('rules_file', 'rules.en.md'), 'r', encoding='utf-8') as f:
                url = paste(f.read(), 'md')
        

            if c:
                await bot.edit(c.message, await _('rules.confirm_rules_text', rules_url=url), reply_markup=rm)
            elif m:
                await bot.reply(m, await _('rules.confirm_rules_text', rules_url=url), reply_markup=rm)
            else:
                raise ValueError("Neither CallbackQuery nor Message provided.")

            return
        
        
        text = await _('menu.menu_text',
            user_id=obj.from_user.id,
        )  
        
        rm = IM()
        rm.add(IB(await _('menu.copy_my_id_btn'), copy_text=CopyTextButton(obj.from_user.id), user_id=0))
        
        if c:
            await bot.edit(m, text, reply_markup=rm)
        elif m:
            await bot.reply(m, text, reply_markup=rm)
            
        else:
            raise ValueError("Neither CallbackQuery nor Message provided.")