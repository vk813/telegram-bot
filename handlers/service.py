from telegram import (
    Update,
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ReplyKeyboardRemove,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler, CallbackQueryHandler, MessageHandler, filters,
)

# Состояния для ConversationHandler
CHOOSE_SERVICE, GET_PHONE, GET_ADDRESS, CHOOSE_TIME, CONFIRM_REPEAT = range(5)

# Старт: показываем, можно повторить заявку или создать новую
async def order_service_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prev = context.user_data.get('last_service')
    if prev:
        await update.message.reply_text(
            f"Хотите повторить прошлую заявку?\n"
            f"Услуга: {prev['service']}\n"
            f"Телефон: {prev['phone']}\n"
            f"Адрес: {prev['address']}\n"
            f"Время: {prev['time']}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Заказать повторно", callback_data="repeat_service")],
                [InlineKeyboardButton("Новая заявка", callback_data="new_service")]
            ])
        )
        return CONFIRM_REPEAT
    else:
        return await choose_service(update, context)

# Обработка выбора "повторить/новая"
async def confirm_repeat_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "repeat_service":
        prev = context.user_data['last_service']
        await query.edit_message_text(
            f"Заявка отправлена повторно!\n"
            f"Услуга: {prev['service']}\nТелефон: {prev['phone']}\nАдрес: {prev['address']}\nВремя: {prev['time']}\n\n"
            f"Ожидайте звонка от менеджера."
        )
        # --- здесь интеграция с CRM/базой/уведомлением менеджеру ---
        return ConversationHandler.END
    else:
        await query.edit_message_text("Выберите тип услуги:")
        return await choose_service(update, context, query=query)

# Выбор услуги
async def choose_service(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    buttons = [
        [InlineKeyboardButton("Замена картриджа", callback_data="service_replace")],
        [InlineKeyboardButton("Диагностика", callback_data="service_diag")],
        [InlineKeyboardButton("Установка фильтра", callback_data="service_install")],
    ]
    if query:
        await query.edit_message_text(
            "Выберите тип услуги:", reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await update.message.reply_text(
            "Выберите тип услуги:", reply_markup=InlineKeyboardMarkup(buttons)
        )
    return CHOOSE_SERVICE

# Сохраняем выбор услуги, спрашиваем телефон
async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service = {
        "service_replace": "Замена картриджа",
        "service_diag": "Диагностика",
        "service_install": "Установка фильтра"
    }.get(query.data, "Сервис")
    context.user_data['service'] = service
    await query.edit_message_text("Укажите ваш номер телефона (пример: +79991234567):")
    return GET_PHONE

# Ввод телефона, спрашиваем адрес
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not phone.startswith('+7') or len(phone) < 10:
        await update.message.reply_text("Пожалуйста, введите корректный телефон, например: +79991234567")
        return GET_PHONE
    context.user_data['phone'] = phone
    await update.message.reply_text("Введите адрес установки или обслуживания:")
    return GET_ADDRESS

# Ввод адреса, предлагаем время
async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    if len(address) < 5:
        await update.message.reply_text("Пожалуйста, введите корректный адрес.")
        return GET_ADDRESS
    context.user_data['address'] = address
    times = [["9:00-12:00", "12:00-15:00"], ["15:00-18:00", "18:00-21:00"]]
    await update.message.reply_text(
        "Выберите удобное время:",
        reply_markup=ReplyKeyboardMarkup(times, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSE_TIME

# Ввод времени, подтверждаем заявку
async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time_slot = update.message.text.strip()
    if time_slot not in ["9:00-12:00", "12:00-15:00", "15:00-18:00", "18:00-21:00"]:
        await update.message.reply_text("Пожалуйста, выберите время из предложенных вариантов.")
        return CHOOSE_TIME
    context.user_data['time'] = time_slot

    # Сохраняем как "последнюю заявку" для повторного заказа
    context.user_data['last_service'] = {
        "service": context.user_data['service'],
        "phone": context.user_data['phone'],
        "address": context.user_data['address'],
        "time": context.user_data['time'],
    }

    await update.message.reply_text(
        f"Ваша заявка принята!\n"
        f"Услуга: {context.user_data['service']}\n"
        f"Телефон: {context.user_data['phone']}\n"
        f"Адрес: {context.user_data['address']}\n"
        f"Время: {context.user_data['time']}\n\n"
        "Ожидайте звонка от нашего менеджера.",
        reply_markup=ReplyKeyboardRemove()
    )
    # --- здесь интеграция с CRM/базой/уведомлением менеджеру ---
    return ConversationHandler.END
