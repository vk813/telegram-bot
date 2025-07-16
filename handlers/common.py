import random
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from constants import (
    WELCOME_EMOJIS, get_main_inline_keyboard, CANCEL_TEXT, BACK_TEXT
)
from database import async_session, User
from utils import send_clean_message as _send_clean_message

def _main_menu_text(user) -> str:
    return (
        f"{random.choice(WELCOME_EMOJIS)} Привет, {user.first_name or 'друг'}!\n\n"
        "Я — Фильтрон, твой эксперт по чистой воде.\n\n"
        "• Добавить фильтр — зарегистрируй новый фильтр, чтобы получать напоминания о замене.\n"
        "• Мои фильтры — смотри статус, историю и фото всех своих фильтров.\n"
        "• Узнать, какой фильтр у меня  - уже есть фильтр, подскажем как его обслуживать.\n"
        "• Подписка — оформи автооплату и регулярную доставку фильтров без лишних забот.\n"
        "• Не знаю что выбрать  — задай любой вопрос: помогу выбрать фильтр, подскажу, где купить, или свяжу с менеджером.\n\n"
        "💧 Всегда чистая вода без хлопот!\n"
        "👇 Выберите нужное действие:"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if update.message:
        try:
            await update.message.delete()
        except Exception as ex:
            logging.warning(f"Не удалось удалить команду /start: {ex}")

    is_new = False
    try:
        async with async_session() as session:
            if not await session.get(User, user.id):
                session.add(User(id=user.id,
                                 username=user.username,
                                 first_name=user.first_name))
                await session.commit()
                is_new = True
    except Exception as e:
        logging.error(f"Ошибка добавления пользователя: {e}")
        await update.effective_message.reply_text(
            "⚠️ Не удалось зарегистрировать вас. Попробуйте позже.")
        return ConversationHandler.END

    if is_new:
        await _send_clean_message(
            update,
            context,
            "Добро пожаловать! Нажмите кнопку ниже, чтобы начать работу.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Начать", callback_data="show_menu")]
            ])
        )
        return ConversationHandler.END

    text = _main_menu_text(user)
    await _send_clean_message(update, context, text, reply_markup=get_main_inline_keyboard())
    return ConversationHandler.END

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет последние сообщения бота по команде /clear"""
    chat_id = update.effective_chat.id
    bot_msgs = context.user_data.get('bot_msgs', [])
    for msg_id in bot_msgs:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as ex:
            logging.warning(f"Ошибка удаления сообщения {msg_id}: {ex}")
    context.user_data['bot_msgs'] = []
    await update.message.reply_text("История бота очищена. Используйте /clear для чистоты ленты.")

async def send_clean_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs):
    chat_id = update.effective_chat.id
    bot_msgs = context.user_data.get('bot_msgs', [])
    for msg_id in bot_msgs:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as ex:
            logging.warning(f"Ошибка удаления сообщения {msg_id}: {ex}")

    sent_msg = None
    if getattr(update, "callback_query", None) and update.callback_query:
        sent_msg = await update.callback_query.message.reply_text(text, **kwargs)
    elif getattr(update, "message", None) and update.message:
        sent_msg = await update.message.reply_text(text, **kwargs)

    if sent_msg:
        context.user_data['bot_msgs'] = [sent_msg.message_id]
    return sent_msg



async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data

    if data == "show":
        from handlers.filter import show_filters
        return await show_filters(update, context)

    if data == "profile":
        from handlers.profile import profile
        return await profile(update, context)

    if data == "referral":
        uid = update.callback_query.from_user.id
        await update.callback_query.edit_message_text(
            f"🎁 Пригласите друзей — и получите бонусы!\n"
            f"Ваша ссылка: https://t.me/YOUR_BOT?start=ref%3D{uid}"
        )
        return ConversationHandler.END

    # При выборе "Добавить фильтр" — запускаем сценарий выбора фильтра
    if data == "register":
        from handlers.my_calendar import start_add_filter
        return await start_add_filter(update, context)
    

    # Если выбрали конкретный тип фильтра — запускаем сценарий с датой
    from constants import MAIN_LABELS
    if data in MAIN_LABELS.keys():
        from handlers.filter import filter_choose_callback
        return await filter_choose_callback(update, context)

    # Подсказки (ℹ️) и подробности о фильтрах
    if data.startswith("hint_") or data.startswith("filter_more_"):
        from handlers.filter import filter_hint_handler
        return await filter_hint_handler(update, context)

    if data.startswith("filter_scheme_"):
        from handlers.filter import filter_scheme_handler
        return await filter_scheme_handler(update, context)

    # Остальные неизвестные callback_data
    logging.warning(f"Неизвестный callback_data: {data}")
    await update.callback_query.answer("Неизвестная команда.", show_alert=True)
    return ConversationHandler.END




async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = getattr(update, 'message', None) or getattr(update, 'callback_query', None)
    if msg:
        await msg.reply_text(
            CANCEL_TEXT,
            reply_markup=get_main_inline_keyboard()
        )
    context.user_data.clear()
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Exception while handling update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Ой, что-то пошло не так. Попробуйте чуть позже."
        )

async def go_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text=BACK_TEXT,
        reply_markup=get_main_inline_keyboard()
    )
    return ConversationHandler.END

async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text=CANCEL_TEXT,
        reply_markup=get_main_inline_keyboard()
    )
    return ConversationHandler.END

async def cancel_calendar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "Операция отменена.",
        reply_markup=get_main_inline_keyboard()
    )
    return ConversationHandler.END

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="Вы вернулись в главное меню.",
        reply_markup=get_main_inline_keyboard()
    )
    return ConversationHandler.END


async def show_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображает главное меню после приветствия."""
    query = update.callback_query
    await query.answer()
    text = _main_menu_text(query.from_user)
    await _send_clean_message(update, context, text, reply_markup=get_main_inline_keyboard())
    return ConversationHandler.END

async def support_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "🤖 Здесь вы можете узнать:\n"
        "• Как выбрать фильтр\n"
        "• Где купить фильтр\n"
        "• Как заказать сервис\n"
        "• Как оформить подписку\n\n"
        "Просто напишите свой вопрос, подскажу и помогу с выбором.\n\n"
        "Если нужна персональная консультация — напишите нашему менеджеру: @vkup25"
    )
    return ConversationHandler.END
