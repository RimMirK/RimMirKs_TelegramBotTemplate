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



from collections import defaultdict
import pytz
from telebot.types import (
    InlineKeyboardMarkup as IM, InlineKeyboardButton as IB,
    ReplyKeyboardMarkup  as RM, KeyboardButton as KB,
    CallbackQuery as C, Message, Message as M,
    CopyTextButton, ReplyKeyboardRemove as KR,
)

from cpytba import CustomAsyncTeleBot as Bot
from database import DB
from translator import get_text_translations, tr
from logging import Logger
from utils import paste
from utils.lang import get_langs_rm

async def main(bot: Bot, db: DB, logger: Logger):
    
    async def flt(msg):
        return msg.text in (await get_text_translations('settings.tz.back_to_settings')).values()
    
    bot.add_command(3, ['settings'], await get_text_translations("cmd_desc.settings"))
    @bot.message_handler(func=flt)
    @bot.message_handler(['settings'])
    @bot.callback_query_handler(c='settings')
    async def _settings(obj: M|C):
        _ = await tr(obj)
        
        if isinstance(obj, M):
            if obj.text == await _("settings.tz.back_to_settings"):
                m = await bot.reply(obj, 'Loading...', reply_markup=KR())
                await bot.delete(m)
        
        user = await db.get_user(obj.from_user.id)
        
        rm = IM()
        rm.add(IB(await _('settings.copy_my_id_btn'), copy_text=CopyTextButton(obj.from_user.id), user_id=0))
        rm.add(IB(await _('settings.change_lang'), callback_data='settings:change_lang', user_id=obj.from_user.id))
        rm.add(IB(await _('settings.change_timezone', timezone=user['timezone']), callback_data='settings:timezone', user_id=obj.from_user.id))

        await bot.answer(obj, await _('settings.text'), reply_markup=rm)
        
    
    timezones = [zone for zone in pytz.all_timezones if '/' in zone]
    country_timezones = defaultdict(list)
    cities = []
    for tz in timezones:
        country, city = tz.split('/', 1)
        cities.append(city)
        country_timezones[country].append(tz)
        del country, city

    timezones = dict(country_timezones)

    duplicates = [x for x in set(cities) if cities.count(x) > 1]
    
    async def flt1(msg):
        return msg.text in (await get_text_translations('settings.tz.back_to_regions')).values()
    
    @bot.callback_query_handler(c='settings:timezone')
    @bot.message_handler(func=flt1)
    @bot.message_handler(['timezone'])
    async def _timezone(obj: M|C):
        _ = await tr(obj)
        
        rm = RM(True, row_width=4)
        rm.add(*[KB(region) for region in timezones.keys()])
        rm.add(KB(await _('settings.tz.back_to_settings')))
        
        await bot.reply(obj if isinstance(obj, M) else obj.message, await _('settings.tz.choose_region'), reply_markup=rm)

        if isinstance(obj, C):
            await bot.answer_callback_query(obj.id)
        
    
    @bot.message_handler(func=lambda m: m.text in list(timezones.keys()))
    async def _tz_region(msg: M):
        _ = await tr(msg)
        
        rm = RM(True, row_width=3)
        rm.add(*[
            KB(tz.removeprefix(msg.text+"/")
               if tz.removeprefix(msg.text+"/") not in duplicates
               else tz
            ) for tz in timezones[msg.text]
        ])
        rm.add(KB(await _('settings.tz.back_to_regions')))
        
        await bot.reply(msg, await _('settings.tz.choose_timezone'), reply_markup=rm)
    
    @bot.callback_query_handler(c='settings:change_lang')
    async def _settings_change_lang(c: C):
        _ = await tr(c)
        rm = IM()
        rm = get_langs_rm(rm, c.from_user.id, 'set_lang')
        rm.add(IB(await _("back.back_btn"), callback_data='settings', user_id=c.from_user.id))
        await bot.edit(
            c.message,
            " • ".join((await get_text_translations('settings.choose_lang', 'choose language')).values()),
            reply_markup=rm
        )
    
    @bot.message_handler(func=lambda m: m.text in (cities + sum(timezones.values(), [])))
    async def _tz(msg: M):
        _ = await tr(msg)
        
        tz = (
            msg.text if '/' in msg.text
            else next((
                entry for country in timezones.values()
                for entry in country
                if msg.text in entry
            ), None)
        )
        await db.set_timezone(msg.from_user.id, tz)
        await bot.reply(msg, await _('settings.tz.timezone_set', timezone=tz), reply_markup=KR())
        return await _settings(msg)