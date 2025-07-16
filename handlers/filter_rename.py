import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters

from database import async_session, Filter
from handlers.filter import show_filters  # Лучше импортировать в начале

RENAME_WAIT = 3303

async def start_rename_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        filter_id = int(query.data.replace("rename_filter_", ""))
    except ValueError:
        await query.edit_message_text("Ошибка: неверный формат ID фильтра.")
        return ConversationHandler.END
    context.user_data["rename_filter_id"] = filter_id
    await query.edit_message_text("Введите новое имя для фильтра (например, 'Кухня', 'Для родителей', 'Дача'):")
    return RENAME_WAIT

async def save_new_filter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text.strip()
    filter_id = context.user_data.get("rename_filter_id")
    if not filter_id or not new_name or len(new_name) < 2:
        await update.message.reply_text("Ошибка. Попробуйте еще раз. Имя должно быть не короче 2 символов.")
        return ConversationHandler.END
    try:
        async with async_session() as session:
            filter_obj = await session.get(Filter, filter_id)
            if not filter_obj:
                await update.message.reply_text("Фильтр не найден.")
                return ConversationHandler.END
            filter_obj.name = new_name
            await session.commit()
        await update.message.reply_text(f"Новое имя фильтра: <b>{new_name}</b>", parse_mode="HTML")
        # Показываем обновленный список
        return await show_filters(update, context)
    except Exception as e:
        logging.error(f"Ошибка при переименовании фильтра: {e}")
        await update.message.reply_text("Ошибка при сохранении имени. Попробуйте позже.")
        return ConversationHandler.END

async def cancel_rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Переименование отменено.")
    return ConversationHandler.END

rename_filter_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_rename_filter, pattern="^rename_filter_")],
    states={
        RENAME_WAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_filter_name)],
    },
    fallbacks=[MessageHandler(filters.COMMAND, cancel_rename)]
)
