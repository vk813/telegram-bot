from telegram import Update, Message
from telegram.ext import ContextTypes

async def delete_bot_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """
    Удаляет все сообщения, id которых сохранены в context.user_data['bot_msgs'].
    """
    bot_msgs = context.user_data.get('bot_msgs', [])
    for msg_id in bot_msgs:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass  # Игнорируем ошибки (например, сообщение уже удалено)
    context.user_data['bot_msgs'] = []

async def send_clean_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs) -> Message:
    """
    Удаляет все предыдущие сообщения бота у пользователя и отправляет новое.
    Возвращает отправленное сообщение.
    """
    chat_id = update.effective_chat.id
    await delete_bot_messages(context, chat_id)

    sent_msg = await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)

    context.user_data['bot_msgs'] = [sent_msg.message_id]
    return sent_msg

async def send_many_clean_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, messages: list) -> list:
    """
    Удаляет все предыдущие сообщения бота у пользователя и отправляет несколько новых.
    messages: список кортежей (text, kwargs_dict)
    Возвращает список объектов Message.
    """
    chat_id = update.effective_chat.id
    await delete_bot_messages(context, chat_id)

    sent_msgs = []
    for text, kwargs in messages:
        sent_msg = await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)
        sent_msgs.append(sent_msg)
    context.user_data['bot_msgs'] = [msg.message_id for msg in sent_msgs]
    return sent_msgs

def add_bot_message_id(context: ContextTypes.DEFAULT_TYPE, message_id: int):
    """
    Добавляет message_id в список сообщений бота для последующего удаления.
    """
    if 'bot_msgs' not in context.user_data:
        context.user_data['bot_msgs'] = []
    context.user_data['bot_msgs'].append(message_id)
