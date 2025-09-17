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



import asyncio
from telebot.types import (
    InlineKeyboardMarkup as IM, InlineKeyboardButton as IB,
    ReplyKeyboardMarkup as RM, KeyboardButton as KB,
    CallbackQuery as C, Message, Message as M,
    CopyTextButton, ReplyKeyboardRemove as RKR
)

from cpytba import CustomAsyncTeleBot as Bot
from database import DB
from translator import get_lang_title, get_langs, get_text_translations, tr, aitranslate, detect_language, jinja_env
from logging import Logger


async def main(bot: Bot, db: DB, logger: Logger):

    
    bot.add_command(4, ['newsletter'], await get_text_translations('cmd_desc.newsletter'), True)
    @bot.callback_query_handler(None, cdata='newsletter', is_admin=True)
    @bot.message_handler(['newsletter'], is_admin=True)
    async def _newsletter(obj: M | C):
        
        _ = await tr(obj)
        
        msg = obj if isinstance(obj, M) else obj.message
        await bot.state(obj, 'newsletter:message')
        if arg := (msg.text.split(maxsplit=1)[1] if len(msg.text.split()) >= 2 else ''):
            if '-important' in arg or '-i' in arg:
                imp = True
                await bot.reply(msg, await _('newsletter.important_mode_enabled'))
                await bot.set_data(obj, important=True)
        else:
            imp = False
        
            await bot.set_data(obj, important=False)
    
        rm = IM()
        rm.add(IB(
            await _('newsletter.switch_important_mode', on=not imp),
            callback_data='newsletter:toggle_important_mode'),
               user_id=obj.from_user.id
        )
    
        await bot.reply(msg, await _('newsletter.write_msg'), reply_markup=rm)
        
    
    @bot.callback_query_handler(None, c='newsletter:toggle_important_mode')
    async def _newsletter_toggle_important_mode(c: C):
        await bot.answer_callback_query(c.id)
        
        data = await bot.get_data(c)
        important = data['important']
        
        _ = await tr(c)
        
        if important:
            await bot.set_data(c, important=False)
            await bot.edit_message_reply_markup(
                c.message.chat.id, c.message.id,
                reply_markup=IM().add(IB(await _("newsletter.switch_important_mode", on=True),
                callback_data='newsletter:toggle_important_mode', user_id=c.from_user.id))
            )
        else:
            await bot.set_data(c, important=True)
            await bot.edit_message_reply_markup(
                c.message.chat.id, c.message.id,
                reply_markup=IM().add(IB(await _("newsletter.switch_important_mode", on=False),
                callback_data='newsletter:toggle_important_mode'), user_id=c.from_user.id)
            )
        
    

        
    @bot.message_handler(state='newsletter:message')
    async def _newsletter_message(msg: M):
        _ = await tr(msg)
        
        await bot.set_data(msg, text=msg.html_text)
        await bot.reply(msg, 
            await _("newsletter.send_one_media"),
            reply_markup=RM(True).add(KB(await _("newsletter.skip"))), quote=True
        )
        await bot.state(msg, 'newsletter:media')
    
    
    @bot.message_handler(state='newsletter:media', content_types=['text', 'photo', 'video', 'animation'])
    async def _newsletter_media(msg: M):
        _ = await tr(msg)
        
        if msg.text and msg.text == await _("newsletter.skip"):
            await bot.set_data(msg, file_type='nomedia', file_id=None)
        else:
            await bot.set_data(msg,
                file_type=(
                    'video' if msg.video
                    else (
                        'gif' if msg.animation
                        else 'photo'
                    )
                ),
                file_id=(msg.animation or msg.video or msg.photo[-1]).file_id
            )
        
        
        await bot.reply(msg, await _('newsletter.add_links'))
        await bot.state(msg, 'newsletter:kb')
    
    @bot.message_handler(state='newsletter:kb')
    async def _newsletter_kb(msg: M):
        _ = await tr(msg)
        if msg.text and msg.text == await _('newsletter.skip'):
            rm = None
        else:
            str_rows = msg.text.split('\n\n\n')
            rm = IM()
            for row in str_rows:
                btns = row.split('\n\n')
                buttons = []
                for btn in btns:
                    buttons.append(IB(*btn.split('\n'), user_id=0))   
                rm.add(*buttons)
        
        await bot.set_data(msg, rm=rm)
        data = await bot.get_data(msg)
        text = data['text']
        file_id = data['file_id']
        file_type = data['file_type']
            
        template = jinja_env.from_string(text)
        rendered_text = await template.render_async(user=msg.from_user, bot=bot, db=db, _=_)
        
        params = dict(
            chat_id = msg.chat.id,
            caption = rendered_text,
            reply_markup = rm,
        )
        
        nid = await db.add_newsletter(msg.from_user.id, text, detect_language(text))
        
        await bot.set_state(msg.from_user.id, f"newsletter:confirm", msg.chat.id)
        
        await bot.reply(msg, await _("newsletter.everything_ok"), reply_markup=RM(True).add(
            KB(f"✅"), KB(f"❌")
        ))
        
        
        match file_type:
            case 'gif':
                sm = await bot.send_animation(**params, animation=file_id)
            case 'photo':
                sm = await bot.send_photo(**params, photo=file_id)
            case 'video':
                sm = await bot.send_video(**params, video=file_id)
            case 'nomedia':
                sm = await bot.reply(msg, params['caption'], reply_markup=rm)
        
        await bot.set_data(msg, nid=nid)
                
        lnrm = IM()
        for lang in get_langs():
            lnrm.add(IB(get_lang_title(lang), callback_data=f'newsletter:translated:{nid}:{lang}:{sm.chat.id}:{sm.id}', user_id=msg.from_user.id))
        
        await bot.reply(msg, await _('newsletter.translations_menu'), reply_markup=lnrm)

            
    @bot.message_handler(state='newsletter:confirm')
    async def _newsletter_confirm(msg: M):
        _ = await tr(msg)
        
        if msg.text == f'✅':
            await bot.reply(msg, await _('newsletter.started'), reply_markup=RKR())
            data = await bot.get_data(msg)
            rm = data['rm']
            text = data['text']
            file_id = data['file_id']
            file_type = data['file_type']
            important = data['important']
            nid = data['nid']
                
            await bot.unstate(msg)
            
            errors = []
            c = 0
            s = 0
            
            async for user in db.get_users(important=important):
                c += 1
                params = dict(
                    chat_id = user['user_id'],
                    caption = text,
                    reply_markup = rm
                )
                try:
                    newsletter = await db.get_newsletter(nid)
                    translated = await aitranslate(newsletter['text'], user['lang'], newsletter['lang'])
                    template = jinja_env.from_string(translated)
                    text = await template.render_async(bot=bot, db=db, _=_)
                    params['caption'] = text
                    match file_type:
                        case 'gif':
                            sm = await bot.send_animation(**params, animation=file_id)
                        case 'photo':
                            sm = await bot.send_photo(**params, photo=file_id)
                        case 'video':
                            sm = await bot.send_video(**params, video=file_id)
                        case 'nomedia':
                            sm = await bot.send_message(user['user_id'], params['caption'], reply_markup=rm)
                    await db.add_newsletter_message(nid, user['user_id'], sm.id)
                    s += 1
                except Exception as ex:
                    errors.append((user['user_id'], ex))
                await asyncio.sleep(.025)
            
            await bot.reply(msg, await _('newsletter.end', c=c, s=s, errors=errors, nid=nid))
            
        else:
            await bot.reply(msg, await _('newsletter.cancelled'), reply_markup=RKR())
            await bot.unstate(msg)
            
            
    @bot.callback_query_handler(None, cs='newsletter:translated:')
    async def _newsletter_translated(c: C):
        _ = await tr(c)
        
        *__, nid, lang, cid, mid = c.data.split(':')
        nid, cid, mid = map(int, (nid, cid, mid))
        
        newsletter = await db.get_newsletter(nid)
        
        translated = await aitranslate(newsletter['text'], lang, newsletter['lang'])
        
        template = jinja_env.from_string(translated)
        text = await template.render_async(bot=bot, db=db, _=_)
        
        await bot.edit_message_text(text, cid, mid)
        
        await bot.answer_callback_query(c.id)
        
        
    bot.add_command(6, ['delete_newsletter'], await get_text_translations('cmd_desc.delete_newsletter'), True)
    @bot.message_handler(['delete_newsletter'], is_admin=True)
    async def _delete_newsletter(msg: M):
        _ = await tr(msg)
        
        if arg := (msg.text.split(maxsplit=1)[1] if len(msg.text.split()) >= 2 else ''):
            try:
                nid = int(arg)
            except:
                await bot.reply(msg, await _('newsletter.delete.invalid_id', nid=arg))
                return

        try:
            newsletter = await db.get_newsletter(nid, with_messages=True)
        except:
            await bot.reply(msg, await _('newsletter.delete.not_found', nid=nid))
            return

        d = 0
        c = 0
        errors = []
        for sm in newsletter.get('messages', []):
            try:
                await bot.delete_message(sm['user_id'], sm['message_id'])
                d += 1
            except Exception as ex:
                errors.append((sm['user_id'], ex))
            c += 1
            await asyncio.sleep(.05)
            
        await bot.reply(msg,
            await _('newsletter.delete.deleted', nid=nid, d=d, c=c, errors=errors)
        )
        
        
    bot.add_command(5, ['edit_newsletter'], await get_text_translations('cmd_desc.edit_newsletter'), True)
    @bot.message_handler(['edit_newsletter'], is_admin=True)
    async def _edit_newsletter(msg: M):
        pass