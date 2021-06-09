#Copyright (C) 2021 Free Software @noobanon @FakeMasked , Inc.[ https://t.me/noobanon https://t.me/FakeMasked ]
#Everyone is permitted to copy and distribute verbatim copies
#of this license document, but changing it is not allowed.
#The GNGeneral Public License is a free, copyleft license for
#software and other kinds of works.
#PTB13 Updated by @noobanon
from typing import Optional

from telegram import Message, Update, Bot, User
from telegram import MessageEntity, ParseMode
from telegram.ext import Filters, MessageHandler, run_async

from marvel import dispatcher
from marvel.modules.disable import DisableAbleCommandHandler, DisableAbleMessageHandler
from marvel.modules.sql import afk_sql as sql
from marvel.modules.users import get_user_id

from marvel.modules.translations.strings import tld

AFK_GROUP = 7
AFK_REPLY_GROUP = 8

def afk(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    args = update.effective_message.text.split(None, 1)
    if len(args) >= 2:
        reason = args[1]
    else:
        reason = ""

    sql.set_afk(update.effective_user.id, reason)
    fname = update.effective_user.first_name
    update.effective_message.reply_text(tld(chat.id, f"{fname} is now AFK!"))



def no_longer_afk(update, context):
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot

    if not user:  # ignore channels
        return

    res = sql.rm_afk(user.id)
    if res:
        firstname = update.effective_user.first_name
        update.effective_message.reply_text(tld(chat.id, f"{firstname} is no longer AFK!"))



def reply_afk(update, context):
    message = update.effective_message  # type: Optional[Message]
    bot = context.bot
    if message.entities and message.parse_entities([MessageEntity.TEXT_MENTION, MessageEntity.MENTION]):
        entities = message.parse_entities([MessageEntity.TEXT_MENTION, MessageEntity.MENTION])
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

            elif ent.type == MessageEntity.MENTION:
                user_id = get_user_id(message.text[ent.offset:ent.offset + ent.length])
                if not user_id:
                    # Should never happen, since for a user to become AFK they must have spoken. Maybe changed username?
                    return
                chat = bot.get_chat(user_id)
                fst_name = chat.first_name

            else:
                return

            check_afk(bot, update, user_id, fst_name)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(bot, update, user_id, fst_name)


def check_afk(bot, update, user_id, fst_name):
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_afk(user_id):
        user = sql.check_afk_status(user_id)
        if not user.reason:
            res = tld(chat.id, f"{fst_name} is AFK!")
        else:
            res = tld(chat.id, f"{fst_name} is AFK! says its because of:\n{user.reason}")
        update.effective_message.reply_text(res)


__help__ = """
 - /afk <reason>: mark yourself as AFK.
 - brb <reason>: same as the afk command - but not a command.

When marked as AFK, any mentions will be replied to with a message to say that you're not available!
"""

__mod_name__ = "AFK"

AFK_HANDLER = DisableAbleCommandHandler("afk", afk)
AFK_REGEX_HANDLER = DisableAbleMessageHandler(Filters.regex("(?i)brb"), afk, friendly="afk")
NO_AFK_HANDLER = MessageHandler(Filters.all & Filters.chat_type.groups, no_longer_afk)
AFK_REPLY_HANDLER = MessageHandler(Filters.all & Filters.chat_type.groups, reply_afk)

dispatcher.add_handler(AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REGEX_HANDLER, AFK_GROUP)
dispatcher.add_handler(NO_AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)
