import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from constants import get_main_inline_keyboard, ADMIN_CHAT_ID
import traceback
from utils import send_clean_message


KNOW_FILTER_PHOTO = 7400

async def start_know_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт диалога 'Узнать фильтр по фото'"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📸 Пожалуйста, отправьте фото вашего фильтра крупным планом. Мы определим модель и расскажем, как его обслуживать.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_know_filter")]
        ])
    )
    return KNOW_FILTER_PHOTO

async def receive_know_filter_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение фото, пересылка админу и сообщение пользователю"""
    try:
        if not update.message.photo:
            await update.message.reply_text(
                "Это не фото. Пожалуйста, отправьте изображение фильтра, чтобы мы могли его идентифицировать.",
                reply_markup=get_main_inline_keyboard()
            )
            return KNOW_FILTER_PHOTO
        photo = update.message.photo[-1]
        file = await photo.get_file()
        user = update.effective_user
        caption = (
            f"👤 Запрос 'Узнать фильтр':\n"
            f"User: {user.first_name or ''} @{user.username or ''} (id: {user.id})"
        )
        await context.bot.send_photo(
            chat_id=int(ADMIN_CHAT_ID),
            photo=file.file_id,
            caption=caption
        )
        await update.message.reply_text(
            "✅ Фото отправлено специалисту! Ожидайте ответа или обратной связи в чате.",
            reply_markup=get_main_inline_keyboard()
        )
    except Exception as e:
        import traceback
        logging.error(f"Ошибка при получении или отправке фото фильтра: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(
            "❗ Ошибка при отправке фото. Попробуйте ещё раз.",
            reply_markup=get_main_inline_keyboard()
        )
    return ConversationHandler.END


async def cancel_know_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Отменено. Чем ещё помочь?",
        reply_markup=get_main_inline_keyboard()
    )
    return ConversationHandler.END

know_filter_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_know_filter, pattern="^know_filter$")],
    states={
        KNOW_FILTER_PHOTO: [MessageHandler(filters.PHOTO, receive_know_filter_photo)],
    },
    fallbacks=[
        CallbackQueryHandler(cancel_know_filter, pattern="^cancel_know_filter$")
    ]
)
