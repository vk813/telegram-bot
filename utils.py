from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import re

logger = logging.getLogger(__name__)

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


def _get_pagination_keyboard(prefix: str, idx: int, total: int) -> InlineKeyboardMarkup | None:
    """Создать клавиатуру пагинации."""
    buttons = []
    if idx > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}_prev"))
    if idx < total - 1:
        buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"{prefix}_next"))
    return InlineKeyboardMarkup([buttons]) if buttons else None


async def split_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, prefix: str = "split"):
    """Отправить длинный текст несколькими сообщениями с пагинацией."""
    parts = [text[i:i + 4096] for i in range(0, len(text), 4096)]
    context.user_data[f"{prefix}_pages"] = parts
    context.user_data[f"{prefix}_idx"] = 0
    markup = _get_pagination_keyboard(prefix, 0, len(parts))
    await send_clean_message(update, context, parts[0], reply_markup=markup)


async def split_message_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для навигации по страницам, созданным split_message."""
    query = update.callback_query
    await query.answer()
    prefix, action = query.data.rsplit("_", 1)
    pages = context.user_data.get(f"{prefix}_pages", [])
    idx = context.user_data.get(f"{prefix}_idx", 0)
    if action == "next" and idx < len(pages) - 1:
        idx += 1
    elif action == "prev" and idx > 0:
        idx -= 1
    context.user_data[f"{prefix}_idx"] = idx
    markup = _get_pagination_keyboard(prefix, idx, len(pages))
    await query.message.edit_text(pages[idx], reply_markup=markup)


def safe_callback_data(data: object) -> str:
    """Return a Telegram-safe callback_data string (<=64 bytes, allowed chars)."""
    orig = data
    if data is None:
        data = ""
    data = str(data)
    # Remove disallowed characters
    data = re.sub(r"[^A-Za-z0-9_-]", "", data)
    # Truncate to 64 bytes
    if len(data.encode("utf-8")) > 64:
        data = data.encode("utf-8")[:64].decode("utf-8", errors="ignore")
    if not data:
        data = "noop"
    logger.info("callback_data=%r", data)
    return data

