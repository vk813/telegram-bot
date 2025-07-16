import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from handlers.common import start

logger = logging.getLogger(__name__)

CANCEL_BUTTON = "❌ Отмена"
PAYMENT_START = range(1)

def safe_handler(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await func(update, context)
        except Exception as e:
            logger.exception("Ошибка в payments.py: %s", e)
            msg = getattr(update, "effective_message", None)
            if msg:
                await msg.reply_text("Ошибка оплаты. Попробуйте позже или обратитесь в поддержку.")
            return ConversationHandler.END
    return wrapper

@safe_handler
async def generate_deep_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Здесь должна быть логика генерации уникальной ссылки на оплату
    # Например, через ЮKassa, Stripe или другой сервис (здесь — заглушка)
    pay_url = "https://pay.example.com/deeplink/your_unique_payment_id"
    keyboard = [
        [InlineKeyboardButton("Оплатить сейчас", url=pay_url)],
        [InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel")]
    ]
    await update.message.reply_text(
        "Для продолжения необходимо оплатить услугу.\n"
        "Нажмите кнопку ниже, чтобы перейти к оплате:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PAYMENT_START

@safe_handler
async def payment_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "Платёж отменён.",
            reply_markup=ReplyKeyboardMarkup([["Главное меню"]], resize_keyboard=True)
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            "Платёж отменён.",
            reply_markup=ReplyKeyboardMarkup([["Главное меню"]], resize_keyboard=True)
        )
    return ConversationHandler.END

payments_conv = ConversationHandler(
    entry_points=[
        CommandHandler("pay", generate_deep_link),
        MessageHandler(filters.Regex("^💳 Оплатить$"), generate_deep_link)
    ],
    states={
        PAYMENT_START: [
            CallbackQueryHandler(payment_cancel, pattern=f"^{CANCEL_BUTTON}$")
        ]
    },
    fallbacks=[
        MessageHandler(filters.Regex(f"^{CANCEL_BUTTON}$"), payment_cancel),
        CallbackQueryHandler(payment_cancel, pattern=f"^{CANCEL_BUTTON}$"),
        CommandHandler("start", start)
    ],
    allow_reentry=True
)
