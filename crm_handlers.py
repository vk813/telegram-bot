from telegram import Update
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
)

CLIENT_NAME, CLIENT_PHONE, CONFIRM_CLIENT = range(3)

async def start_add_client(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Введите имя клиента:")
    return CLIENT_NAME

async def handle_client_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['client_name'] = update.message.text
    await update.message.reply_text("Введите телефон клиента:")
    return CLIENT_PHONE

async def handle_client_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['client_phone'] = update.message.text
    name = context.user_data['client_name']
    phone = context.user_data['client_phone']
    await update.message.reply_text(f"Имя: {name}\nТелефон: {phone}\n\nПодтвердить? (да/нет)")
    return CONFIRM_CLIENT

async def confirm_client(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() in ['да', 'yes', 'y']:
        await update.message.reply_text("Клиент добавлен!")
        # тут можно добавить запись в БД
    else:
        await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

crm_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('addclient', start_add_client)],
    states={
        CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_client_name)],
        CLIENT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_client_phone)],
        CONFIRM_CLIENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_client)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    per_message=False,
)
