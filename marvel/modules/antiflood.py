#Copyright (C) 2021 Free Software @noobanon @FakeMasked , Inc.[ https://t.me/noobanon https://t.me/FakeMasked ]
#Everyone is permitted to copy and distribute verbatim copies
#of this license document, but changing it is not allowed.
#The GNGeneral Public License is a free, copyleft license for
#software and other kinds of works.
#PTB13 Updated by @noobanon﻿

import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, CommandHandler, run_async
from telegram.utils.helpers import mention_html
from  marvel.modules.helper_funcs.string_handling import extract_time
from  marvel.modules.helper_funcs.extraction import extract_user_and_text 
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery

from  marvel import dispatcher
from  marvel.modules.helper_funcs.chat_status import is_user_admin, user_admin, can_restrict, user_can_change
from  marvel.modules.log_channel import loggable
from  marvel.modules.sql import antiflood_sql as sql
from  marvel.modules.connection import connected
from  marvel.modules.translations.strings import tld
from  marvel.modules.sql.approve_sql import is_approved
FLOOD_GROUP = 3


 
@loggable
def check_flood(update, context) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    bot = context.bot
   
    if not user:  # ignore channels
        return ""

    # ignore admins
    if is_user_admin(chat, user.id):
        sql.update_flood(chat.id, None)
        return ""
    # ignore approved
    if is_approved (chat.id, user.id):
        return ""

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""
    try:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            chat.kick_member(user.id)
            execstrings = tld(update.effective_message, "Get Out!")
            tag = "BANNED"
        elif getmode == 2:
            chat.kick_member(user.id)
            chat.unban_member(user.id)
            execstrings = tld(update.effective_message, "Kicked!")
            tag = "KICKED"
        elif getmode == 3:
            bot.restrict_chat_member(chat.id, user.id, can_send_messages=False)
            execstrings = tld(update.effective_message, "Now you silent!")
            tag = "MUTED"
        elif getmode == 4:
            bantime = extract_time(msg, getvalue)
            chat.kick_member(user.id, until_date=bantime)
            execstrings = tld(update.effective_message, "Tᴇᴍᴘ Bᴀɴɴᴇᴅ ᴛɪʟʟ {}" ).format(getvalue)
            tag = "TBAN"
        elif getmode == 5:
            mutetime = extract_time(msg, getvalue)
            bot.restrict_chat_member(chat.id, user.id, until_date=mutetime, can_send_messages=False)
            execstrings = tld(update.effective_message, "Mᴜᴛᴇᴅ ᴛɪʟʟ {}" ).format(getvalue)
            tag = "TMUTE"
        reply = "{} i like babycorn you like flooding we are not same bro so *{}* in {}".format(mention_html(user.id, user.first_name), execstrings, chat.title)
        msg.reply_text(reply, parse_mode=ParseMode.HTML)
        
        return "#MUTED" \
               "\n<b>Chat:</b> {}" \
               "\n<b>User:</b> {}" \
               "\nFlooded the group.".format(html.escape(chat.title),
                                             mention_html(user.id, user.first_name))

    except BadRequest:
        msg.reply_text(tld(chat.id, "I can't Mute people here, give me permissions first! Until then, I'll disable antiflood."))
        sql.set_flood(chat.id, 0)
        return "#INFO" \
               "\n<b>Chat:</b> {}" \
               "\nDon't have Mute permissions, so automatically disabled antiflood.".format(chat.title)


 
@user_admin
@can_restrict
@user_can_change
@loggable
def set_flood(update, context) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    bot = context.bot
    args = context.args

    if len(args) >= 1:
        val = args[0].lower()
        if val == "off" or val == "no" or val == "0":
            sql.set_flood(chat.id, 0)
            message.reply_text(tld(chat.id, "Antiflood has been disabled."))

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat.id, 0)
                message.reply_text(tld(chat.id,  "Antiflood has been disabled."))
                return "#SETFLOOD" \
                       "\n<b>Chat:</b> {}" \
                       "\n<b>Admin:</b> {}" \
                       "\nDisabled antiflood.".format(html.escape(chat.title), mention_html(user.id, user.first_name))

            elif amount < 3:
                message.reply_text(tld(chat.id, "Antiflood has to be either 0 (disabled), or a number bigger than 3 (enabled)!"))
                return ""

            else:
                sql.set_flood(chat.id, amount)
                message.reply_text(tld(chat.id, "Antiflood has been updated and set to {}").format(amount))
                return "#SETFLOOD" \
                       "\n<b>Chat:</b> {}" \
                       "\n<b>Admin:</b> {}" \
                       "\nSet antiflood to <code>{}</code>.".format(html.escape(chat.title),
                                                                    mention_html(user.id, user.first_name), amount)

        else:
            message.reply_text(tld(chat.id, "Unrecognised argument - please use a number, 'off', or 'no'."))

    return ""


 
def flood(update, context):
    chat = update.effective_chat  # type: Optional[Chat]

    limit = sql.get_flood_limit(chat.id)
    if limit == 0:
        update.effective_message.reply_text(tld(chat.id, "I'm not currently enforcing flood control!"))
    else:
        update.effective_message.reply_text(tld(chat.id,
            "I'm currently Muting users if they send more than {} consecutive messages.").format(limit))

 
@user_admin
@user_can_change
def set_flood_mode(update, context): 
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    bot = context.bot
    args = context.args

    conn = connected(bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            update.effective_message.reply_text(tld(update.effective_message, "Use This Command in Groups,NOT in PM"))
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() == 'ban':
            settypeflood = tld(update.effective_message, 'Banned')
            sql.set_flood_strength(chat_id, 1, "0")
        elif args[0].lower() == 'kick':
            settypeflood = tld(update.effective_message, 'Kicked')
            sql.set_flood_strength(chat_id, 2, "0")
        elif args[0].lower() == 'mute':
            settypeflood = tld(update.effective_message, 'Muted')
            sql.set_flood_strength(chat_id, 3, "0")
        elif args[0].lower() == 'tban':
            if len(args) == 1:
                teks = tld(update.effective_message, """It looks like you tried to set a time value for the anti-flood, but did not specify a time; use `/setfloodmode tban <timevalue>`.
Examples of the value of time: 4m = 4 minute, 3h = 3 Hours, 6d = 6 days, 5w = 5 weeks.""")
                msg.reply_text(teks, parse_mode="markdown")
                return
            settypeflood = tld(update.effective_message, "temporarily ban during {}").format(args[1])
            sql.set_flood_strength(chat_id, 4, str(args[1]))
        elif args[0].lower() == 'tmute':
            if len(args) == 1:
                teks = tld(update.effective_message, """It looks like you tried to set a time value for the anti-flood, but did not specify a time; use `/setfloodmode tban <timevalue>`.
Examples of the value of time: 4m = 4 minute, 3h = 3 Hours, 6d = 6 days, 5w = 5 weeks.""")
                msg.reply_text(teks, parse_mode="markdown")
                return
            settypeflood = tld(update.effective_message, 'temporarily mute during {}').format(args[1])
            sql.set_flood_strength(chat_id, 5, str(args[1]))
        else:
            msg.reply_text(tld(update.effective_message, "I understand only ban/kick/mute/tban/tmute"))
            return
        if conn:
            text = tld(update.effective_message, "Too many sent messages Result Will Be `{}` on *{}*!").format(settypeflood, chat_title)
        else:
            text = tld(update.effective_message, "Too many sent messages Result Will Be `{}`!").format(settypeflood)
        msg.reply_text(text, parse_mode="markdown")
        return "<b>{}:</b>\n" \
                "<b>Admin:</b> {}\n" \
                "Has changed antiflood mode. User will {}.".format(settypeflood, html.escape(chat.title),
                                                                            mention_html(user.id, user.first_name))
    else:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            settypeflood = tld(update.effective_message, 'banned')
        elif getmode == 2:
            settypeflood = tld(update.effective_message, 'kick')
        elif getmode == 3:
            settypeflood = tld(update.effective_message, 'mute')
        elif getmode == 4:
            settypeflood = tld(update.effective_message, 'Blocking while during {}'.format(getvalue))
        elif getmode == 5:
            settypeflood = tld(update.effective_message, 'temporarily mute during {}'.format(getvalue))
        if conn:
            text = tld(update.effective_message, "If the member sends a message straight, then he will *di {}* on *{}*.").format(settypeflood, chat_name)
        else:
            text = tld(update.effective_message, "If the member sends a message straight, then he will *di {}*.").format(settypeflood)
        msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    return ""
   
        
def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(bot, update, chat, chatP, user):
    chat_id = chat.id
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "*Not* currently enforcing flood control."
    else:
        return "Antiflood is set to `{}` messages.".format(limit)


__help__ = """
 - /flood: Get the current flood control setting
*Admin only:*
 - /setflood <int/'no'/'off'>: enables or disables flood control

 - /setfloodmode tmute/tban/mute/ban
 *Example* `/setfloodmode tmute 5m`
"""

__mod_name__ = "AntiFlood"

FLOOD_BAN_HANDLER = MessageHandler(Filters.all & ~Filters.status_update & Filters.chat_type.groups, check_flood, run_async=True)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, pass_args=True, filters=Filters.chat_type.groups, run_async=True)
FLOOD_HANDLER = CommandHandler("flood", flood, filters=Filters.chat_type.groups)
SET_FLOOD_MODE_HANDLER = CommandHandler("setfloodmode", set_flood_mode, pass_args=True, filters=Filters.chat_type.groups, run_async=True)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)
dispatcher.add_handler(SET_FLOOD_MODE_HANDLER)
