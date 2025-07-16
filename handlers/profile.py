import re
import logging
from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ContextTypes, MessageHandler, filters,
    CallbackQueryHandler, ConversationHandler, CommandHandler
)
from database import async_session, User
from constants import get_main_inline_keyboard, PROFILE_EDIT, PROFILE_PHONE, PROFILE_EMAIL
from utils import send_clean_message


# Логгер для отслеживания ошибок
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
ASK_PHONE, CONFIRM_PHONE = range(2)
CANCEL_BUTTON = "❌ Отмена"

END = ConversationHandler.END

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Профиль — просмотр"""
    user_id = update.callback_query.from_user.id
    try:
        async with async_session() as session:
            user = await session.get(User, user_id)
    except Exception as e:
        logging.error(f"Ошибка получения профиля: {e}")
        await update.callback_query.edit_message_text("Ошибка доступа к профилю.")
        return END
    if not user:
        await update.callback_query.edit_message_text("Пользователь не найден. /start")
        return END

    text = (
        f"👤 <b>Профиль</b>\n"
        f"Имя: {user.first_name or '-'}\n"
        f"Username: @{user.username or '-'}\n"
        f"Телефон: {user.phone or '-'}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Изменить телефон", callback_data="edit_phone")],
        [InlineKeyboardButton("✉️ Изменить e-mail", callback_data="edit_email")],
        [InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")]
    ])
    await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
    return PROFILE_EDIT

async def edit_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.edit_message_text(
        "📱 Введите новый номер телефона (пример: +79991234567):",
    )
    return PROFILE_PHONE

async def edit_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.edit_message_text(
        "✉️ Введите e-mail:",
    )
    return PROFILE_EMAIL

async def save_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not re.match(r"^(\+7|8)\d{10}$", text):
        await update.message.reply_text(
            "😅 Неверный формат. Попробуйте ещё раз или /cancel.",
            reply_markup=ForceReply(selective=True)
        )
        return PROFILE_PHONE

    user_id = update.effective_user.id
    try:
        async with async_session() as session:
            user = await session.get(User, user_id)
            if user:
                user.phone = text
                await session.commit()
            else:
                await update.message.reply_text("Используйте /start.")
                return END
    except Exception as e:
        await update.message.reply_text(
            "❗ Ошибка при сохранении. Попробуйте ещё раз или /cancel.",
            reply_markup=ForceReply(selective=True)
        )
        logging.error(f"Ошибка при сохранении телефона: {e}")
        return PROFILE_PHONE

    await update.message.reply_text(
        f"✅ Телефон сохранён: {text}",
        reply_markup=get_main_inline_keyboard()
    )
    context.user_data.clear()
    return END

async def save_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", text):
        await update.message.reply_text(
            "😅 Неверный формат e-mail. Попробуйте ещё раз или /cancel.",
            reply_markup=ForceReply(selective=True)
        )
        return PROFILE_EMAIL

    user_id = update.effective_user.id
    try:
        async with async_session() as session:
            user = await session.get(User, user_id)
            if user:
                # ! ВНИМАНИЕ: добавь поле email в модель User!
                user.email = text
                await session.commit()
            else:
                await update.message.reply_text("Используйте /start.")
                return END
    except Exception as e:
        await update.message.reply_text(
            "❗ Ошибка при сохранении. Попробуйте ещё раз или /cancel.",
            reply_markup=ForceReply(selective=True)
        )
        logging.error(f"Ошибка при сохранении email: {e}")
        return PROFILE_EMAIL

    await update.message.reply_text(
        f"✅ E-mail сохранён: {text}",
        reply_markup=get_main_inline_keyboard()
    )
    context.user_data.clear()
    return END

async def cancel_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Операция отменена.", reply_markup=get_main_inline_keyboard())
    context.user_data.clear()
    return END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Действие отменено. Если хотите — начните заново через /start.",
        reply_markup=ReplyKeyboardMarkup([["Главное меню"]], resize_keyboard=True)
    )
    return ConversationHandler.END

phone_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(edit_phone, pattern="^edit_phone$"),
        CallbackQueryHandler(edit_email, pattern="^edit_email$")
    ],
    states={
        PROFILE_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_phone)],
        PROFILE_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_email)],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_phone),
        CallbackQueryHandler(cancel_phone, pattern="^back_to_menu$"),
    ],
    per_message=False
)
