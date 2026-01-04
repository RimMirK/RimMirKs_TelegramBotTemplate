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


import json
from typing import AsyncGenerator, List
from logging import Logger
import time as time_mod
import time

import aiosqlite

from utils import format_date
from config import DEFAULT_LANG
 
 
class DB:
    path: str
    con: aiosqlite.Connection
    logger: Logger

    def __init__(self, path) -> None:
        self.path = path
        self.con = None
    

    async def bootstrap(self) -> None:
        if not self.con:
            self.con = await aiosqlite.connect(self.path)
            
    async def force_bootstrap(self) -> None:
        if self.con:
            await self.con.close()
        self.con = await aiosqlite.connect(self.path)

    async def teardown(self) -> None:
        await self.con.close()
        
    async def sql(self, sql: str, asdict: bool = False, return_cursor=False, **params) -> list | dict:
        self.logger.debug(f"Executing sql {sql!r} with params {params}")
        cursor = await self.con.execute(sql, params)
        rows = await cursor.fetchall()
        
        if asdict and return_cursor:
            raise ValueError("Cannot return cursor and asdict at the same time.")
        
        if asdict:
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        
        await self.con.commit()
        self.logger.debug(f"Executed sql {sql!r} with params {params}. result: {rows}")
        
        if return_cursor:
            return cursor
        
 
        return rows
 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

    async def create_tables(self):
        
        await self.sql(f"""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY
                                        NOT NULL,
                user_id         INTEGER UNIQUE
                                        NOT NULL,
                reg             NUMERIC,
                lang            TEXT    DEFAULT {DEFAULT_LANG},
                timezone        TEXT    DEFAULT UTC,
                rules_confirmed INTEGER DEFAULT (0),
                banned          INTEGER DEFAULT (0),
                is_admin        INTEGER DEFAULT (0),
                newsletter      INTEGER DEFAULT (1) 
            );
        """)
        await self.sql("""
            CREATE TABLE IF NOT EXISTS errors (
                id      INTEGER PRIMARY KEY,
                error   TEXT    NOT NULL,
                time    INTEGER,
                user_id INTEGER REFERENCES users (user_id) 
            );
        """)
        await self.sql("""
            CREATE TABLE IF NOT EXISTS newsletters (
                id      INTEGER PRIMARY KEY,
                user_id INTEGER REFERENCES users (user_id),
                text    TEXT    NOT NULL,
                time    NUMERIC,
                lang    TEXT,
                sent    INTEGER DEFAULT (0) 
            );
        """)
        await self.sql("""
            CREATE TABLE IF NOT EXISTS newsletters_messages (
                id            INTEGER PRIMARY KEY,
                newsletter_id         REFERENCES newsletters (id) NOT NULL,
                user_id               REFERENCES users (user_id)  NOT NULL,
                message_id    INTEGER                             NOT NULL,
                time          NUMERIC
            );            
        """)
        await self.sql("""    
            CREATE TABLE IF NOT EXISTS translated_newsletters (
                id            INTEGER PRIMARY KEY,
                newsletter_id INTEGER REFERENCES newsletters (id),
                text          TEXT,
                lang          TEXT
            );
        """)
        await self.sql("""
            CREATE TABLE IF NOT EXISTS cache (
                func TEXT NOT NULL,
                args TEXT NOT NULL,
                kwargs TEXT NOT NULL,
                result TEXT NOT NULL,
                PRIMARY KEY (func, args, kwargs)
            );
        """)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
 
    # CACHE #
    async def add_cache(self, func_name: str, args: tuple, kwargs: dict, result):
        await self.sql(
            """
            INSERT OR REPLACE INTO cache(func, args, kwargs, result)
            VALUES (:func, :args, :kwargs, :result)
            """,
            func=func_name,
            args=json.dumps(args, ensure_ascii=False),
            kwargs=json.dumps(kwargs, ensure_ascii=False),
            result=json.dumps(result, ensure_ascii=False),
        )

    async def get_cache(self, func_name: str, args: tuple, kwargs: dict):
        row = await self.sql(
            """
            SELECT result FROM cache
            WHERE func = :func AND args = :args AND kwargs = :kwargs
            LIMIT 1
            """,
            func=func_name,
            args=json.dumps(args, ensure_ascii=False),
            kwargs=json.dumps(kwargs, ensure_ascii=False),
            asdict=True,
        )
        if row:
            return json.loads(row["result"])
        return None

    # USERS #
 
    async def register(self, user_id: int, reg: float = None) -> bool:
        cursor = await self.sql(
            "INSERT OR IGNORE INTO users (user_id, reg) VALUES (:user_id, :reg)",
            user_id=user_id,
            reg=reg or time.time(),
            return_cursor=True
        )
        return cursor.rowcount > 0
    async def is_registered(self, user_id: int) -> bool:
        return not not (await self.sql("SELECT user_id FROM users WHERE user_id=:user_id", user_id=user_id))
    
    async def get_user(self, user_id: int) -> dict:
        user = await self.sql("SELECT * FROM users WHERE user_id=:user_id LIMIT 1", user_id=user_id, asdict=True)
        if not user:
            return {}
        user: dict = user[0]
        if user['reg']:
            user['reg_str'] = format_date(user['reg'])
        return user
    
    async def ban_user(self, user_id: int) -> None:
        await self.sql("UPDATE users SET banned = 1 WHERE user_id = :user_id", user_id=user_id)
    
    async def unban_user(self, user_id: int) -> None:
        await self.sql("UPDATE users SET banned = 0 WHERE user_id = :user_id", user_id=user_id)
    
    async def is_banned(self, user_id: int) -> bool:
        return not not (await self.sql("SELECT banned FROM users WHERE user_id=:user_id", user_id=user_id))[0][0]
    
    async def is_admin(self, user_id: int) -> bool:
        return not not (await self.sql("SELECT is_admin FROM users WHERE user_id=:user_id", user_id=user_id))[0][0]
    
    async def get_admins(self) -> List[int]:
        return [a[0] for a in ((await self.sql('SELECT user_id FROM users WHERE is_admin=1')) or [])]

    async def get_users(self, important=False) -> AsyncGenerator[dict, None]:
        query = "SELECT * from users" if important else "SELECT * from users where newsletter = true" 
        for row in await self.sql(query, asdict=True):
            yield row
    
    async def get_users_count(self) -> int:
        return (await self.sql("SELECT COUNT(*) FROM users"))[0][0]
            
    # LANGUAGES #
    
    async def get_lang(self, user_id: int) -> str:
        return (await self.sql("SELECT lang FROM users WHERE user_id=:user_id", user_id=user_id))[0][0]
    
    async def set_lang(self, user_id: int, lang: str) -> None:
        await self.sql("UPDATE users SET lang = :lang where user_id = :user_id", lang=lang, user_id=user_id)


    # TIMEZONES #
    
    async def set_timezone(self, user_id: int, timezone: str) -> None:
        await self.sql("UPDATE users SET timezone = :timezone WHERE user_id=:user_id", user_id=user_id, timezone=timezone) 

    # RULES #

    async def is_rules_confirmed(self, user_id: int) -> bool:
        return not not (await self.sql("SELECT rules_confirmed FROM users WHERE user_id=:user_id", user_id=user_id))[0][0]
    
    async def set_rules_confirmed(self, user_id: int) -> None:
        await self.sql("UPDATE users SET rules_confirmed = 1 WHERE user_id = :user_id", user_id=user_id)


    # ERRORS # 
    
    async def add_error(self, error: str, user_id: int) -> int:
        cursor = await self.sql("INSERT INTO errors (error, time, user_id) VALUES (:error, :time, :user_id)", error=error, time=time.time(), user_id=user_id, return_cursor=True)
        return cursor.lastrowid
    
    async def get_error(self, eid: int) -> dict:
        error = await self.sql("SELECT * FROM errors WHERE id=:eid LIMIT 1", eid=eid, asdict=True)
        if not error:
            return {}
        error: dict = error[0]
        if error['time']:
            error['time_str'] = format_date(error['time'])
        return error

    # NEWSLETTER #
    
    async def add_newsletter(self, user_id: int, text: str, lang: str, time: float=None, sent: bool=None) -> int:
        cur = await self.sql("INSERT INTO newsletters (user_id, text, lang, time, sent) "
                                             "VALUES (:user_id,:text,:lang,:time,:sent)",
                       user_id=user_id, text=text, lang=lang, time=time or time_mod.time(), sent=sent, return_cursor=True)
        return cur.lastrowid
    
    async def get_newsletter(self, nid: int, with_messages: bool = False) -> dict:
        rows = await self.sql("SELECT * FROM newsletters WHERE id = :nid", nid=nid, asdict=True)
        if with_messages and rows:
            rows[0]['messages'] = await self.sql("SELECT * FROM newsletters_messages WHERE newsletter_id = :nid", nid=nid, asdict=True)
        return rows[0]
    
    async def add_newsletter_message(self, nid: int, user_id: int, message_id: int, time: float=None) -> int:
        await self.sql("INSERT INTO newsletters_messages (newsletter_id, user_id, message_id, time) "
                                                "VALUES (:newsletter_id,:user_id,:message_id,:time)",
            newsletter_id=nid, user_id=user_id, message_id=message_id, time=time or time_mod.time())
    


db = DB('database.db')