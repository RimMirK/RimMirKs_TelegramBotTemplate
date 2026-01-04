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

### EDIT HERE ###
##  vvvvvvvvv  ##

AI_TRANSLATE_BOT_DESCRIPTION = """

"""

DEFAULT_LANG = "ru"

LOG_CHAT_ID = -10012345678

LOG_REGISTER = True
LOG_ERRORS = True

LOG_REGISTER_TEMPLATE = """
<b>NEW USER</b>

ID: <code>{{ user.id }}</code>
Name: {{ user.full_name }}
Username: {{ "@"+user.username if user.username else "-"}}
Premium: {{ "Yes" if user.is_premium else "No" }}
Link: {{ user.link|safe }}

#newuser #u{{ user.id }}
"""
LOG_ERRORS_TEMPLATE = """
<b>ERROR</b> {{ "(callback)" if is_callback else "" }}

<b>ID</b>: <code>{{ eid }}</code>
<b>USER</b>: {{ user_link|safe }} [<code>{{ user_id }}</code>]
<b>TIME</b>: <b>{{ time_str }}</b> [{{ time }}]
<b>URL</b>: {{ paste(traceback, "py", True) }}
<b>TRACEBACK</b>:
<pre language="python">{% if traceback|length > 2000 %}
{{ traceback[:1000] ~ "\n\n...\n\n" ~ traceback[-1000:] }}
{% else %}
{{ traceback }}
{% endif %}
</pre>

#error #u{{ user_id }}
"""

##  ^^^^^^^^^  ##
### EDIT HERE ###

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_TOKEN")


if __name__ == "__main__":
    raise RuntimeError("To change the config, open config.py for *editing* instead of running")