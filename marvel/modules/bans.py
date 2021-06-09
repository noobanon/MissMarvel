#Copyright (C) 2021 Free Software @noobanon @FakeMasked , Inc.[ https://t.me/noobanon https://t.me/FakeMasked ]
#Everyone is permitted to copy and distribute verbatim copies
#of this license document, but changing it is not allowed.
#The GNGeneral Public License is a free, copyleft license for
#software and other kinds of works.
#PTB13 Updated by @noobanon

import html
import time
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html
from telegram import ParseMode

from marvel import dispatcher, BAN_STICKER, LOGGER, OWNER_ID
from marvel.modules.disable import DisableAbleCommandHandler
from marvel.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_bot_admin, can_delete, user_can_ban
from marvel.modules.helper_funcs.extraction import extract_user_and_text
from marvel.modules.helper_funcs.string_handling import extract_time
from marvel.modules.log_channel import loggable
from marvel.modules.helper_funcs.filters import CustomFilters

from marvel.modules.translations.strings import tld


@bot_admin
@can_restrict
@user_can_ban
@user_admin
@loggable
def ban(update, context) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    bot = context.bot
    args = context.args

    user_id, reason = extract_user_and_text(message, args)
    

    if not user_id:
        message.reply_text(tld(chat.id, "You don't seem to be referring to a user."))
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text(tld(chat.id, "I can't seem to find this user"))
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text(tld(chat.id, "I'm not gonna BAN myself, are you crazy?"))
        return ""
    
    if user_id == 1091139479:
        message.reply_text(tld(chat.id, "Someone trying to ban my master and act like pro #LMAO i got a noob and its you"))
        return ""

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text(tld(chat.id, "Why would I ban an admin? That sounds like a pretty dumb idea."))
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        reply = "Admin {} Banned User {} in {}!".format(mention_html(user.id, user.first_name),
                                                        mention_html(member.user.id, member.user.first_name), chat.title)
        bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML)                    
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(tld(chat.id, "Banned!"), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text(tld(chat.id, "Banned!"))

    return ""


@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def temp_ban(update, context) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    bot = context.bot
    args = context.args

    user_id, reason = extract_user_and_text(message, args)
    
    time.sleep(2)
    message.delete()

    if can_delete(chat, bot.id):
        try:
            update.effective_message.reply_to_message.delete()
        except AttributeError:
            pass

    if not user_id:
        message.reply_text(tld(chat.id, "You don't seem to be referring to a user."))
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text(tld(chat.id, "I can't seem to find this user"))
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text(tld(chat.id, "This user is ban protected, meaning that you cannot ban this user!"))
        return ""

    if user_id == bot.id:
        message.reply_text(tld(chat.id, "I'm not gonna BAN myself, are you crazy?"))
        return ""

    if not reason:
        message.reply_text(tld(chat.id, "You haven't specified a time to ban this user for!"))
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)" \
          "\n<b>Time:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name),
                                     member.user.id,
                                     time_val)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)
        reply = "{} has been temporarily banned for {}!".format(mention_html(member.user.id, member.user.first_name),time_val)
        bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML)
        return log


    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
            message.reply_text(tld(chat.id, "Banned! User will be banned for {}.").format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text(tld(chat.id, "Banned!"))

    return ""

@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def kick(update, context) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    bot = context.bot
    args = context.args

    user_id, reason = extract_user_and_text(message, args)
    
    time.sleep(2)
    message.delete()

    if can_delete(chat, bot.id):
        try:
            update.effective_message.reply_to_message.delete()
        except AttributeError:
            pass

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("I'm not kicking myself!")
        return ""

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Why would I kick an admin? That sounds like a pretty dumb idea.")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        reply = "{} Kicked!".format(mention_html(member.user.id, member.user.first_name))
        bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML)
         
        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>Admin:</b> {}" \
              "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                           mention_html(user.id, user.first_name),
                                                           mention_html(member.user.id, member.user.first_name),
                                                           member.user.id)
        if reason:
            log += "\n<b>Reason:</b> {}".format(reason)

        return log

    else:
        message.reply_text("Kicked!")

    return ""


@bot_admin
@can_restrict
def kickme(update, context):
    user_id = update.effective_message.from_user.id
    bot = context.bot
    args = context.args
    if user_id == OWNER_ID:
        update.effective_message.reply_text("Oof, I can't kick my master.")
        return
    elif is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Why would I kick an admin? That sounds like a pretty dumb idea.")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("No problem.")
    else:
        update.effective_message.reply_text("Huh? I can't :/")


@bot_admin
@can_restrict
@loggable
def banme(update, context):
    user_id = update.effective_message.from_user.id
    chat = update.effective_chat
    user = update.effective_user
    bot = context.bot
    if user_id == OWNER_ID:
        update.effective_message.reply_text("Oof, I can't ban my master.")
        return
    elif is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Why would I ban an admin? That sounds like a pretty dumb idea.")
        return

    res = update.effective_chat.kick_member(user_id)  
    if res:
        update.effective_message.reply_text("No problem, banned.")
        log = "<b>{}:</b>" \
              "\n#BANME" \
              "\n<b>User:</b> {}" \
              "\n<b>ID:</b> <code>{}</code>".format(html.escape(chat.title),
                                                    mention_html(user.id, user.first_name), user_id)
        return log

    else:
        update.effective_message.reply_text("Huh? I can't :/")

@bot_admin
@can_restrict
@user_admin
@loggable
def unban(update, context) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    args = context.args

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("How would I unban myself if I wasn't here...?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("Why are you trying to unban someone that's already in the chat?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("Yep, this user can join!")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    return log

@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def sban(update, context) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    bot = context.bot
    args = context.args

    update.effective_message.delete()

    user_id, reason = extract_user_and_text(message, args)
    
    time.sleep(2)
    message.delete()

    if can_delete(chat, bot.id):
        try:
            update.effective_message.reply_to_message.delete()
        except AttributeError:
            pass


    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        return ""

    if user_id == bot.id:
        return ""

    log = "<b>{}:</b>" \
          "\n# SILENTBAN" \
          "\n<b>• Admin:</b> {}" \
          "\n<b>• User:</b> {}" \
          "\n<b>• ID:</b> <code>{}</code>".format(html.escape(chat.title), mention_html(user.id, user.first_name), 
                                                  mention_html(member.user.id, member.user.first_name), user_id)
    if reason:
        log += "\n<b>• Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id, excp.message)       
    return ""


__help__ = """
Some people need to be publicly banned; spammers, annoyances, or just trolls.

This module allows you to do that easily, by exposing some common actions, so everyone will see!

Available commands are:
 - /ban: bans a user from your chat.
 - /banme: ban yourself
 - /tban: temporarily bans a user from your chat. set time using int<d/h/m> (days hours minutes)
 - /unban: unbans a user from your chat.
 - /sban: silently bans a user. (via handle, or reply)
 - /mute: mute a user in your chat.
 - /tmute: temporarily mute a user in your chat. set time using int<d/h/m> (days hours minutes)
 - /unmute: unmutes a user from your chat.
 - /kick: kicks a user from your chat.
 - /kickme: users who use this, kick themselves!

 An example of temporarily muting someone:
/tmute @username 2h; this mutes a user for 2 hours.
"""

__mod_name__ = "Bans"

BAN_HANDLER = DisableAbleCommandHandler("ban", ban, pass_args=True, filters=Filters.chat_type.groups, admin_ok=True, run_async=True)
TEMPBAN_HANDLER = DisableAbleCommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.chat_type.groups, admin_ok=True, run_async=True)
KICK_HANDLER = DisableAbleCommandHandler("kick", kick, pass_args=True, filters=Filters.chat_type.groups, admin_ok=True)
UNBAN_HANDLER = DisableAbleCommandHandler("unban", unban, pass_args=True, filters=Filters.chat_type.groups, admin_ok=True, run_async=True)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.chat_type.groups)
SBAN_HANDLER = DisableAbleCommandHandler("sban", sban, pass_args=True, filters=Filters.chat_type.groups, admin_ok=True, run_async=True)
BANME_HANDLER = DisableAbleCommandHandler("banme", banme, filters=Filters.chat_type.groups, run_async=True)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(BANME_HANDLER)
dispatcher.add_handler(SBAN_HANDLER)
