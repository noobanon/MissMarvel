#Copyright (C) 2021 Free Software @noobanon @FakeMasked , Inc.[ https://t.me/noobanon https://t.me/FakeMasked ]
#Everyone is permitted to copy and distribute verbatim copies
#of this license document, but changing it is not allowed.
#The GNGeneral Public License is a free, copyleft license for
#software and other kinds of works.
#PTB13 Updated by @noobanon

from typing import Union, List, Optional

from future.utils import string_types
from telegram import ParseMode, Update, Bot, Chat, User, MessageEntity
from telegram.ext import CommandHandler, Filters, MessageHandler, Filters
from telegram.utils.helpers import escape_markdown

from marvel import dispatcher
from marvel.modules.helper_funcs.handlers import CMD_STARTERS
from marvel.modules.helper_funcs.misc import is_module_loaded

from marvel.modules.translations.strings import tld

from marvel.modules.connection import connected

FILENAME = __name__.rsplit(".", 1)[-1]

# If module is due to be loaded, then setup all the magical handlers
if is_module_loaded(FILENAME):
    from marvel.modules.helper_funcs.chat_status import user_admin, is_user_admin
    from telegram.ext.dispatcher import run_async

    from marvel.modules.sql import disable_sql as sql

    DISABLE_CMDS = []
    DISABLE_OTHER = []
    ADMIN_CMDS = []

    class DisableAbleCommandHandler(CommandHandler):
        def __init__(self, command, callback, admin_ok=False, **kwargs):
            super().__init__(command, callback, **kwargs)
            self.admin_ok = admin_ok
            if isinstance(command, string_types):
                DISABLE_CMDS.append(command)
                if admin_ok:
                    ADMIN_CMDS.append(command)
            else:
                DISABLE_CMDS.extend(command)
                if admin_ok:
                    ADMIN_CMDS.extend(command)
            sql.disableable_cache(command)

        def check_update(self, update):
            if isinstance(update, Update) and update.effective_message:
                message = update.effective_message

                if (message.entities and message.entities[0].type == MessageEntity.BOT_COMMAND
                        and message.entities[0].offset == 0):
                    command = message.text[1:message.entities[0].length]
                    args = message.text.split()[1:]
                    command = command.split('@')
                    command.append(message.bot.username)

                    if not (command[0].lower() in self.command
                            and command[1].lower() == message.bot.username.lower()):
                        return None

                    filter_result = self.filters(update)
                    if filter_result:
                        chat = update.effective_chat
                        user = update.effective_chat
                        # disabled, admincmd, user admin
                        if sql.is_command_disabled(chat.id, command[0].lower()):
                            # check if command was disabled
                            is_disabled = command[0] in ADMIN_CMDS and is_user_admin(chat, user.id)
                            if not is_disabled and sql.is_disable_del(chat.id):
                                # disabled and should delete
                                update.effective_message.delete()
                            if not is_disabled:
                                return None
                            else:
                                return args, filter_result

                        return args, filter_result
                    else:
                        return False



    class DisableAbleMessageHandler(MessageHandler):
        def __init__(self, pattern, callback, friendly="", **kwargs):
            super().__init__(pattern, callback, **kwargs)
            DISABLE_OTHER.append(friendly or pattern)
            sql.disableable_cache(friendly or pattern)
            self.friendly = friendly or pattern

        def check_update(self, update):
            if isinstance(update, Update) and update.effective_message:
                chat = update.effective_chat
                return self.filters(update) and not sql.is_command_disabled(chat.id, self.friendly)

    
    @user_admin
    def disable(update, context):
        chat = update.effective_chat  # type: Optional[Chat]
        user = update.effective_user  # type: Optional[User]
        bot = context.bot
        args = context.args
    
        conn = connected(bot, update, chat, user.id)
        if not conn == False:
            chatD = dispatcher.bot.getChat(conn)
        else:
            if chat.type == "private":
                exit(1)
            else:
                chatD = update.effective_chat

        if len(args) >= 1:
            disable_cmd = args[0]
            if disable_cmd.startswith(CMD_STARTERS):
                disable_cmd = disable_cmd[1:]

            if disable_cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                sql.disable_command(chatD.id, disable_cmd)
                update.effective_message.reply_text(tld(chat.id, "Disabled the use of `{}` in *{}*").format(disable_cmd, chatD.title),
                                                    parse_mode=ParseMode.MARKDOWN)
            else:
                update.effective_message.reply_text(tld(chat.id, "That command can't be disabled"))

        else:
            update.effective_message.reply_text(tld(chat.id, "What should I disable?"))

    @user_admin
    def enable(update, context):
        chat = update.effective_chat  # type: Optional[Chat]
        user = update.effective_user  # type: Optional[User]
        bot = context.bot
        args = context.args
    
        conn = connected(bot, update, chat, user.id)
        if not conn == False:
            chatD = dispatcher.bot.getChat(conn)
        else:
            if chat.type == "private":
                exit(1)
            else:
                chatD = update.effective_chat

        if len(args) >= 1:
            enable_cmd = args[0]
            if enable_cmd.startswith(CMD_STARTERS):
                enable_cmd = enable_cmd[1:]

            if sql.enable_command(chatD.id, enable_cmd):
                update.effective_message.reply_text(tld(chat.id, "Enabled the use of `{}` in *{}*").format(enable_cmd, chatD.title),
                                                    parse_mode=ParseMode.MARKDOWN)
            else:
                update.effective_message.reply_text(tld(chat.id, "Is that even disabled?"))

        else:
            update.effective_message.reply_text(tld(chat.id, "What should I enable?"))
            
    
    def list_cmds(update, context):
        chat = update.effective_chat  # type: Optional[Chat]
        bot = context.bot
        if DISABLE_CMDS + DISABLE_OTHER:
            result = ""
            for cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                result += " • `{}`\n".format(escape_markdown(cmd))
            update.effective_message.reply_text(tld(chat.id, "The following commands are toggleable:\n{}").format(result),
                                                parse_mode=ParseMode.MARKDOWN)
        else:
            update.effective_message.reply_text(tld(chat.id, "No commands can be disabled."))


    # do not async
    def build_curr_disabled(chatD_id, chat_id):

        disabled = sql.get_all_disabled(chatD_id)

        result = ""
        for cmd in disabled:
            result += " • `{}`\n".format(escape_markdown(cmd))

        if result == "":
            return tld(chat_id, "No commands are disabled!")
        else:
            return result


    
    def commands(update, context):
        chat = update.effective_chat
        user = update.effective_user  # type: Optional[User]
        bot = context.bot
    
        conn = connected(bot, update, chat, user.id, need_admin=False)
        if not conn == False:
            chatD = dispatcher.bot.getChat(conn)
        else:
            if chat.type == "private":
                exit(1)
            else:
                chatD = update.effective_chat

        disabled = sql.get_all_disabled(chatD.id)
        if not disabled:
            update.effective_message.reply_text(tld(chat.id, "No commands are disabled! in *{}*!").format(chatD.title))

        text = build_curr_disabled(chatD.id, chat.id)

        update.effective_message.reply_text(tld(chat.id, "The following commands are currently restricted in *{}*:\n{}").format(chatD.title, text), parse_mode=ParseMode.MARKDOWN)


    def __stats__():
        return "{} disabled items, across {} chats.".format(sql.num_disabled(), sql.num_chats())


    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)


    def __chat_settings__(bot, update, chat, chatP, user):
        return build_curr_disabled(chat.id, chat.id)


    __mod_name__ = "Disableable"

    __help__ = """
Not everyone wants every feature that rose offers. Some commands are best left unused; to avoid spam and abuse.

This allows you to disable some commonly used commands, so noone can use them. It'll also allow you to autodelete them, stopping people from

Available commands are:
 - /disable <commandname>: stop users from using the "commandname" command in this group.
 - /enable <commandname>: allow users to use the "commandname" command in this group again.
 - /listcmds: list all disableable commands.
 - /disabled: list the disabled commands in this chat.

Note:
When disabling a command, the command only gets disabled for non-admins. All admins can still use those commands.
Disabled commands are still accessible through the /connect feature. If you would be interested to see this disabled too, let me know in the support chat.
    """

    DISABLE_HANDLER = CommandHandler("disable", disable, run_async=True)
    ENABLE_HANDLER = CommandHandler("enable", enable, run_async=True)
    COMMANDS_HANDLER = CommandHandler(["cmds", "disabled"], commands, run_async=True)
    TOGGLE_HANDLER = CommandHandler("listcmds", list_cmds, run_async=True)

    dispatcher.add_handler(DISABLE_HANDLER)
    dispatcher.add_handler(ENABLE_HANDLER)
    dispatcher.add_handler(COMMANDS_HANDLER)
    dispatcher.add_handler(TOGGLE_HANDLER)

else:
    DisableAbleCommandHandler = CommandHandler
    DisableAbleMessageHandler = MessageHandler
