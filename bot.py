import os
import logging
import constants
from constants import *

from database import init_db

from datetime import time, timedelta, timezone

from dotenv import load_dotenv


from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters
)

from handlers.common import (
    start,
    handle_callback,
    cancel,
    error_handler,
    go_back_callback,
    cancel_callback,
    main_menu_callback,
    show_menu_callback,
    support_ai,
    clear_history
)


from handlers.my_calendar import reg_conv, cancel_calendar_handler

from handlers.profile import phone_conv, profile, edit_phone

from handlers.filter import (
    show_filters,
    filter_hint_handler,
    filter_scheme_handler,
    filter_choose_callback,
    handle_choose_date
)

from handlers.my_calendar import start_add_filter

from handlers.reminders import send_reminders

from handlers.filter_action import filter_action_handler

from handlers.filter_photo import (
    wait_for_filter_photo,
    add_filter_photo,
    delete_filter_photo,
    add_filter_photo_conv,
    show_filter_photos,
    photo_pagination_callback,
    view_photos_callback,
    send_current_photo,
    del_photo_pagination,
    del_photo_confirm
)

from handlers.filter_rename import rename_filter_conv

from handlers.filter_autoorder import autoorder_handler

from handlers.service import (
    order_service_start,
    confirm_repeat_service,
    ask_phone, get_phone,
    get_address,
    get_time,
    CHOOSE_SERVICE,
    GET_PHONE,
    GET_ADDRESS,
    CHOOSE_TIME,
    CONFIRM_REPEAT
)
from handlers.help import ai_help_handler

#from handlers.support_ai import handle_ai_question

from handlers.know_filter import know_filter_conv

from handlers.subscription import (
    subscription_start,
    subscription_interest,
    subscription_filter_step,
    subscription_contact_step,
    subscription_photo_handler
)

from logging.handlers import RotatingFileHandler


DEBUG = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")

# --- Conversation Handlers ---


filter_add_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            filter_choose_callback,
            # Cовпадение по callback_data для всех фильтров
            pattern="^(osmo_set|cart_uf|post_ugol|ugol|mech|mineral|kuvshin)$"
        ),
    ],
    states={
        CHOOSING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choose_date)],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"),
        CallbackQueryHandler(cancel_callback, pattern="^cancel$"),
    ]
)

service_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^(Заказать сервис)$"), order_service_start)],
    states={
        CONFIRM_REPEAT: [CallbackQueryHandler(confirm_repeat_service, pattern="^confirm_repeat$")],
        CHOOSE_SERVICE: [CallbackQueryHandler(ask_phone, pattern="^choose_service$")],
        GET_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        GET_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
        CHOOSE_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CallbackQueryHandler(cancel_callback, pattern="^cancel$"),
        CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"),
    ]
)


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.DEBUG,
    handlers=[
        RotatingFileHandler("bot.log", maxBytes=10_000_000, backupCount=5, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    # Загрузка переменных окружения и настройка логирования
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN не найден. Проверьте файл .env!")
        exit(1)
    bot_token = bot_token.strip()
    constants.VK_CONTACT = os.getenv("VK_CONTACT", "")

    # Инициализация приложения и БД
    try:
        app = ApplicationBuilder().token(bot_token).post_init(init_db).build()
    except Exception as e:
        logger.error(f"Ошибка инициализации приложения: {e}")
        print("⚠️ Сервис временно недоступен. Попробуйте позже.")
        exit(1)


    # --- Handlers ---
    app.add_handler(reg_conv)
    app.add_handler(phone_conv)
    app.add_handler(add_filter_photo_conv)
    app.add_handler(rename_filter_conv)
    app.add_handler(service_conv) 
    app.add_handler(know_filter_conv)
    app.add_handler(filter_add_conv)


    app.add_handler(CallbackQueryHandler(view_photos_callback, pattern=r"^view_photos_\d+$"))
    app.add_handler(CallbackQueryHandler(delete_filter_photo, pattern=r"^del_photo_\d+$"))
    app.add_handler(CallbackQueryHandler(del_photo_pagination, pattern="^del_photo_(prev|next)$"))
    app.add_handler(CallbackQueryHandler(del_photo_confirm, pattern="^del_photo_confirm$"))
    app.add_handler(CallbackQueryHandler(filter_choose_callback, pattern="^(osmo_set|cart_uf|post_ugol|ugol|mech|mineral|kuvshin)$"))

    app.add_handler(CallbackQueryHandler(wait_for_filter_photo, pattern="^add_photo_"))
    app.add_handler(CallbackQueryHandler(start_add_filter, pattern="^register$"))
    app.add_handler(CallbackQueryHandler(ai_help_handler, pattern="^ai_help$"))
    app.add_handler(CallbackQueryHandler(filter_hint_handler, pattern=r"^(hint_|filter_more_)"))
    app.add_handler(CallbackQueryHandler(filter_scheme_handler, pattern=r"^filter_scheme_"))

 

    app.add_handler(CallbackQueryHandler(subscription_start, pattern="^subscriptions$"))
    app.add_handler(CallbackQueryHandler(subscription_interest, pattern="^subscription_(yes|no)$"))
    app.add_handler(CallbackQueryHandler(subscription_filter_step, pattern="^subscription_(photo|dontknow)$"))
    app.add_handler(CallbackQueryHandler(subscription_contact_step, pattern="^subscription_contact$"))

 
    app.add_handler(CallbackQueryHandler(photo_pagination_callback, pattern="^photo_(prev|next)$"))
    app.add_handler(CallbackQueryHandler(show_filter_photos, pattern="^show_my_photos$"))

    
    app.add_handler(CallbackQueryHandler(filter_action_handler, pattern="^(filter_delete_|filter_replaced_).*"))
    app.add_handler(CallbackQueryHandler(show_filters, pattern="^filter_"))
    app.add_handler(CallbackQueryHandler(go_back_callback, pattern="^go_back$"))
    app.add_handler(CallbackQueryHandler(cancel_calendar_handler, pattern="^calendar_cancel$"))
    app.add_handler(CallbackQueryHandler(cancel_callback, pattern="^cancel$"))
    app.add_handler(CallbackQueryHandler(show_menu_callback, pattern="^show_menu$"))

    app.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^back_to_menu$"))

    app.add_handler(MessageHandler(filters.PHOTO, subscription_photo_handler))

    #app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_question))

    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("my_photos", show_filter_photos))
    app.add_handler(CommandHandler("edit_phone", edit_phone))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)


    # DEBUG-режим — включать только при необходимости!
    if DEBUG:
        async def debug_all(update, context):
            if update.message:
                await update.message.reply_text(f"DEBUG: текст={update.message.text!r}")
            elif update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.message.reply_text(f"DEBUG: callback={update.callback_query.data!r}")
        app.add_handler(MessageHandler(filters.ALL, debug_all))
        app.add_handler(CallbackQueryHandler(debug_all))

    # Ежедневные напоминания
    moscow_time = time(hour=9, minute=0, tzinfo=timezone(timedelta(hours=3)))
    async def scheduled_reminders(context):
        await send_reminders(context)
    app.job_queue.run_daily(
        scheduled_reminders,
        time=moscow_time,
        days=(0,1,2,3,4,5,6),
        name="reminder_job"
    )

    print("Бот запущен! Ожидаю команды...")
    app.run_polling()

if __name__ == "__main__":
    main()
