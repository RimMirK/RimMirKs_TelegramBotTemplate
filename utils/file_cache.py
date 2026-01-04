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
import os
import json
from functools import wraps
from threading import Lock

_cache_locks = {}

def file_cache(cache_dir=".cache"):
    os.makedirs(cache_dir, exist_ok=True)

    def decorator(func):
        cache_file = os.path.join(cache_dir, f"{func.__name__}.cache.json")
        _cache_locks[cache_file] = _cache_locks.get(cache_file) or Lock()

        # Загружаем существующий кэш
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                try:
                    cache_data = json.load(f)
                except json.JSONDecodeError:
                    cache_data = []
        else:
            cache_data = []

        def save_cache():
            with _cache_locks[cache_file]:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)

        # Проверяем, асинхронная ли функция
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                for entry in cache_data:
                    if entry["args"] == args and entry["kwargs"] == kwargs:
                        return entry["result"]

                result = await func(*args, **kwargs)
                cache_data.append({
                    "args": args,
                    "kwargs": kwargs,
                    "result": result
                })
                save_cache()
                return result
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                for entry in cache_data:
                    if entry["args"] == args and entry["kwargs"] == kwargs:
                        return entry["result"]

                result = func(*args, **kwargs)
                cache_data.append({
                    "args": args,
                    "kwargs": kwargs,
                    "result": result
                })
                save_cache()
                return result

        return wrapper
    return decorator
