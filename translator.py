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


import glob
from logging import getLogger
import os
import yaml
from functools import lru_cache

import os

def read_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    return data


trans_data = {}
for file in glob.glob("translations/*.yaml"):
    ln = os.path.splitext(os.path.basename(file))[0]
    yaml_data = read_yaml(file)
    trans_data[ln] = yaml_data

def get_langs():
    return tuple(trans_data.keys())

def get_lang_title(lang):
    return trans_data[lang].get('__title__')


from jinja2 import Environment, StrictUndefined

jinja_env = Environment(
    undefined=StrictUndefined,
    trim_blocks=True,
    autoescape=True,
    enable_async=True
)

import inspect
import utils

jinja_env.globals.update({
    name: obj
    for name, obj in vars(utils).items()
    if inspect.isfunction(obj)
})

def plural_ru(n: int, forms: tuple[str, str, str]) -> str:
    n = abs(n) % 100
    if 11 <= n <= 19:
        return forms[2]
    i = n % 10
    if i == 1:
        return forms[0]
    if 2 <= i <= 4:
        return forms[1]
    return forms[2]

jinja_env.globals['plural_ru'] = plural_ru
jinja_env.globals['hasattr'] = hasattr

class Translator:
    def __init__(self, lang, data):
        self.lang = lang
        self.data = data
        self.logger = getLogger('BOT').getChild("translator")

    async def __call__(self, key, default="Error: translation not found!", **kwargs) -> str:
        keys = key.split(".")
        current = self.data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        text = current


        if kwargs:
            try:
                template = jinja_env.from_string(text)
                text = await template.render_async(**kwargs, Translator=self, _=self, self_=self)
            except Exception as e:
                self.logger.error("Something wrong in translation", exc_info=True)
                raise e

        return text

@lru_cache
def get_translator(lang):
    return Translator(lang, trans_data.get(lang, {}))

@lru_cache
def get_all_trans(key):
    translations = {}
    for lang in trans_data.keys():
        translator = get_translator(lang)
        translations[lang] = translator(key)
    return translations


from telebot.types import Message, Message as M, CallbackQuery, CallbackQuery as C

async def tr(obj: M|C|Message|CallbackQuery) -> Translator:
    """
    Get translator by Message or CallbackQuery
    
    Args:
        obj: Message or CallbackQuery object
        
    Returns:
        Translator
    """
    from database import db
    lang = await db.get_lang(obj.from_user.id)
    return get_translator(lang)

async def get_text_translations(key: str, default="") -> dict:
    def key_exists(d, keys):
        current = d
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return False
        return True

    keys = key.split(".")
    if not any(key_exists(d, keys) for d in trans_data.values()):
        return default

    return {lang: await get_translator(lang)(key, default) for lang in trans_data}



# AI TRANSLATOR 

from langdetect import detect, DetectorFactory
from utils.file_cache import file_cache

DetectorFactory.seed = 0  # ensures consistent results

@file_cache()
def detect_language(text: str) -> str:
    """
    Detects the language of the given text.
    Returns a language code, e.g., 'en', 'ru', 'fr'.
    """
    try:
        return detect(text)
    except:
        return "unknown"


import re
from google import genai
from config import GEMINI_API_KEY, AI_TRANSLATE_BOT_DESCRIPTION

gemini = genai.Client(api_key=GEMINI_API_KEY)

@file_cache()
async def aitranslate(text: str, to_lang: str, from_lang: str = None) -> str:
    """
    Translate text with Gemini while preserving Jinja2 and Markdown.

    :param text: source text
    :param to_lang: target language (e.g. "en", "uk", "pl")
    :param from_lang: Optional. Source language (e.g. "en", "uk", "pl"). Default auto-detect
    :return: translated text
    """

    # 1. Protect Jinja2
    jinja_pattern = re.compile(r"({{.*?}}|{%-?.*?-%}|{#.*?#})", re.DOTALL)
    jinja_parts = {}
    def jinja_replacer(m):
        key = f"__JINJA_{len(jinja_parts)}__"
        jinja_parts[key] = m.group(0)
        return key
    safe_text = jinja_pattern.sub(jinja_replacer, text)


    # 3. Gemini request
    
    from_lang = from_lang or detect_language(safe_text)

    prompt = f"""
You are a professional translator with expertise in writing clear, concise, and natural messages for Telegram bots. 

Translate the following text from {from_lang} into {to_lang}. 

Requirements:
- Preserve placeholders exactly as they appear (__JINJA_X__, __MD_X__, etc.).
- Keep all HTML formatting intact.
- Maintain the original tone, style, and intent suitable for friendly, informative, or instructional bot messages.
- Avoid adding extra commentary or explanations.

Bot context:
{AI_TRANSLATE_BOT_DESCRIPTION}

Text to translate:
{safe_text}
"""
    response = await gemini.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    translated = response.text.strip()


    # 5. Restore Jinja2
    for k, v in jinja_parts.items():
        translated = translated.replace(k, v)

    return translated
