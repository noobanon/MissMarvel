#Copyright (C) 2021 Free Software @noobanon @FakeMasked , Inc.[ https://t.me/noobanon https://t.me/FakeMasked ]
#Everyone is permitted to copy and distribute verbatim copies
#of this license document, but changing it is not allowed.
#The GNGeneral Public License is a free, copyleft license for
#software and other kinds of works.
#PTB13 Updated by @noobanon

from functools import wraps
from time import perf_counter
from typing import Optional
from cachetools import TTLCache	
from threading import RLock
from telegram import User, Chat, ChatMember, Update, Bot

from marvel import DEL_CMDS, SUDO_USERS, WHITELIST_USERS
import marvel.modules.sql.admin_sql as admin_sql
from marvel.modules.translations.strings import tld

from marvel.mwt import MWT

# stores admemes in memory for 10 min.	
ADMIN_CACHE = TTLCache(maxsize=512, ttl=60 * 10, timer=perf_counter)	
THREAD_LOCK = RLock()	

def can_delete(chat: Chat, bot_id: int) -> bool:
    return chat.get_member(bot_id).can_delete_messages


def is_user_ban_protected(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    if chat.type == 'private' \
            or user_id in SUDO_USERS \
            or user_id in WHITELIST_USERS \
            or chat.all_members_are_administrators or user_id in (1087968824, 1091139479):
        return True

    if not member:
        member = chat.get_member(user_id)
    return member.status in ('administrator', 'creator')


def is_user_admin(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    if (
        chat.type == "private"
        or user_id in SUDO_USERS
        or chat.all_members_are_administrators
        or user_id in [777000, 1087968824]
    ):  # Count telegram and Group Anonymous as admin
        return True
    if not member:
        with THREAD_LOCK:
            # try to fetch from cache first.
            try:
                return user_id in ADMIN_CACHE[chat.id]
            except KeyError:
                # keyerror happend means cache is deleted,
                # so query bot api again and return user status
                # while saving it in cache for future useage...
                chat_admins = dispatcher.bot.getChatAdministrators(chat.id)
                admin_list = [x.user.id for x in chat_admins]
                ADMIN_CACHE[chat.id] = admin_list

                return user_id in admin_list
    else:
        return member.status in ("administrator", "creator")

def is_bot_admin(chat: Chat, bot_id: int, bot_member: ChatMember = None) -> bool:
    if chat.type == 'private' \
            or chat.all_members_are_administrators:
        return True

    if not bot_member:
        bot_member = chat.get_member(bot_id)
    return bot_member.status in ('administrator', 'creator')


def is_user_in_chat(chat: Chat, user_id: int) -> bool:
    member = chat.get_member(user_id)
    return member.status not in ('left', 'kicked')


def bot_can_delete(func):
    @wraps(func)
    def delete_rights(update, context, *args, **kwargs):
        if can_delete(update.effective_chat, context.bot.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text("I can't delete messages here! "
                                                "Make sure I'm admin and can delete other user's messages.")

    return delete_rights


def can_pin(func):
    @wraps(func)
    def pin_rights(update, context, *args, **kwargs):
        if update.effective_chat.get_member(context.bot.id).can_pin_messages:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text("I can't pin messages here! "
                                                "Make sure I'm admin and can pin messages.")

    return pin_rights


def can_promote(func):
    @wraps(func)
    def promote_rights(update, context, *args, **kwargs):
        if update.effective_chat.get_member(context.bot.id).can_promote_members:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text("I can't promote/demote people here! "
                                                "Make sure I'm admin and can appoint new admins.")

    return promote_rights


def can_restrict(func):
    @wraps(func)
    def promote_rights(update, context, *args, **kwargs):
        if update.effective_chat.get_member(context.bot.id).can_restrict_members:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text("I can't restrict people here! "
                                                "Make sure I'm admin and can appoint new admins.")

    return promote_rights


def bot_admin(func):
    @wraps(func)
    def is_admin(update, context, *args, **kwargs):
        if is_bot_admin(update.effective_chat, context.bot.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text("I'm not admin!")

    return is_admin

def sudo_user(func):
    @wraps(func)
    def is_admin(update, context, *args, **kwargs):
        user = update.effective_user  # type: Optional[User]
        if user.id in SUDO_USERS:
            return func(update, context, *args, **kwargs)

        elif not user:
            pass

        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

        else:
            update.effective_message.reply_text(languages.tl(update.effective_message, "This command is restricted to my sudo users only."))

    return is_admin

def user_admin(func):
    @wraps(func)
    def is_admin(update, context, *args, **kwargs):
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        if user and is_user_admin(update.effective_chat, user.id):
            return func(update, context, *args, **kwargs)

        elif not user:
            pass

        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

        elif (admin_sql.command_reaction(chat.id) == True):
            update.effective_message.reply_text("Who dis non-admin telling me what to do?")

    return is_admin


def user_admin_no_reply(func):
    @wraps(func)
    def is_admin(update, context, *args, **kwargs):
        user = update.effective_user  # type: Optional[User]
        if user and is_user_admin(update.effective_chat, user.id):
            return func(update, context, *args, **kwargs)

        elif not user:
            pass

        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

    return is_admin


def user_not_admin(func):
    @wraps(func)
    def is_not_admin(update, context, *args, **kwargs):
        user = update.effective_user  # type: Optional[User]
        if user and not is_user_admin(update.effective_chat, user.id):
            return func(update, context, *args, **kwargs)

    return is_not_admin

def user_can_ban(func):

    @wraps(func)
    def user_banner(update, context, *args, **kwargs):

        
        user = update.effective_user.id
        member = update.effective_chat.get_member(user)

        if not (member.can_restrict_members or
                member.status == "creator") and not user in SUDO_USERS:
            update.effective_message.reply_text(
                "You are missing the following rights to use this command: \nCanRestrictUsers.")
            return ""

        return func(update, context, *args, **kwargs)

    return user_banner


def user_can_delete(func):	

    @wraps(func)	
    def message_deleter(update, context, *args, **kwargs):	                         	
        	
        user = update.effective_user.id	
        member = update.effective_chat.get_member(user)
        

        if not (member.can_delete_messages or member.status == "creator") and not user in SUDO_USERS:
            update.effective_message.reply_text("You are missing the following rights to use this command: \nCanDeleteMessages")	
            return ""	
             

        return func(update, context, *args, **kwargs)	

    return message_deleter

def user_can_pin(func):	

    @wraps(func)	
    def message_pinner(update, context, *args, **kwargs):	                         	
        	
        user = update.effective_user.id	
        member = update.effective_chat.get_member(user)
        

        if not (member.can_pin_messages or member.status == "creator") and not user in SUDO_USERS:
            update.effective_message.reply_text("You are missing the following rights to use this command: \nCanPinMessages")	
            return ""	

        return func(update, context, *args, **kwargs)	

    return message_pinner

def user_can_change(func):	

    @wraps(func)	
    def info_changer(update, context, *args, **kwargs):	
        user = update.effective_user.id	
        member = update.effective_chat.get_member(user)	
        

        if not (member.can_change_info or member.status == "creator") and not user in SUDO_USERS:
            update.effective_message.reply_text("You are missing the following rights to use this command: \nCanChangeInfo")
                   	
            return ""	

        return func(update, context, *args, **kwargs)	

    return info_changer

def user_can_promote(func):	

    @wraps(func)	
    def permoter(update, context, *args, **kwargs):		
        user = update.effective_user.id	
        member = update.effective_chat.get_member(user)	
        

        if not (member.can_promote_members or member.status == "creator") and not user in SUDO_USERS:
            update.effective_message.reply_text("You are missing the following rights to use this command: \nCanPromoteUsers")	
            return ""	

        return func(update, context, *args, **kwargs)	

    return permoter
