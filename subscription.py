import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
import time
from telegram.ext import ContextTypes, ConversationHandler
import logging
from constants import CANCEL_BUTTON

logger = logging.getLogger(__name__)

YOUR_MANAGER_ID = int(os.getenv("MANAGER_ID", "660442813"))

import time

DEBOUNCE_SECONDS = 2

# Клавиатуры
cancel_markup = ReplyKeyboardMarkup([[CANCEL_BUTTON]], resize_keyboard=True)
main_menu_markup = ReplyKeyboardMarkup([["Главное меню"]], resize_keyboard=True)


def safe_handler(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await func(update, context)
        except Exception as e:
            logger.exception("Ошибка в handler: %s", e)
            msg = getattr(update, "effective_message", None)
            if msg:
                await msg.reply_text("Что-то пошло не так. Попробуйте еще раз или напишите /start.")
            return ConversationHandler.END
    return wrapper


async def subscription_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = time.time()
    last_click = context.user_data.get('last_click', 0)
    if now - last_click < DEBOUNCE_SECONDS:
        return  # игнорировать повтор
    context.user_data['last_click'] = now


# Старт подписки — из меню (callback_data="subscriptions")
async def subscription_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data="subscription_yes"),
            InlineKeyboardButton("❌ Нет", callback_data="subscription_no")
        ]
    ]
    await update.callback_query.edit_message_text(
        "💧 Мы предлагаем сервисное обслуживание систем очистки воды (замена фильтров, напоминания, всё под ключ).\n\n"
        "1️⃣ Интересно ли вам получать напоминания о замене фильтров и сервис с выездом мастера?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Ответ на "Да/Нет"
async def subscription_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "subscription_no":
        await query.edit_message_text("Спасибо за ответ! Если что — всегда на связи. Хорошего дня!")
        return
    # если "Да"
    keyboard = [
        [InlineKeyboardButton("Прикрепить фото", callback_data="subscription_photo")],
        [InlineKeyboardButton("Не знаю модель", callback_data="subscription_dontknow")]
    ]
    await query.edit_message_text(
        "2️⃣ Какая у вас сейчас система или модель фильтра?\nЕсли не знаете — нажмите соответствующую кнопку или прикрепите фото.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Фото/Не знаю
async def subscription_filter_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # Сохраняем в context.user_data если нужно
    if query.data == "subscription_dontknow":
        context.user_data['filter_info'] = "Не знаю"
    else:
        context.user_data['filter_info'] = "Ожидаем фото"  # Следующий шаг — загрузка фото через обычный MessageHandler

    # Просим телефон
    keyboard = [
        [InlineKeyboardButton("Отправить Telegram-контакт", callback_data="subscription_contact")]
    ]
    await query.edit_message_text(
        "3️⃣ Оставьте ваш телефон или Telegram, чтобы наш менеджер мог связаться с вами.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# Универсальный обработчик отмены:
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Действие отменено. Вы всегда можете начать заново через меню.",
        reply_markup=ReplyKeyboardMarkup([["Главное меню"]], resize_keyboard=True)
    )
    return ConversationHandler.END




# Контакт
async def subscription_contact_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    text = (
        f"📝 Новая заявка на подписку\n"
        f"Пользователь: {user.full_name} (@{user.username}, id={user.id})\n"
        f"Система/модель фильтра: {context.user_data.get('filter_info', '-')}\n"
        f"Контакт: через Telegram"
    )
    await context.bot.send_message(chat_id=YOUR_MANAGER_ID, text=text)
    await query.edit_message_text("Спасибо! Наш менеджер свяжется с вами в ближайшее время.")

# Обработка фото (в отдельном MessageHandler)
async def subscription_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.photo[-1].file_id
    user = update.effective_user
    text = (
        f"📝 Новая заявка на подписку\n"
        f"Пользователь: {user.full_name} (@{user.username}, id={user.id})\n"
        f"Фото фильтра: {file_id}"
    )
    await context.bot.send_message(chat_id=YOUR_MANAGER_ID, text=text)
    await context.bot.send_photo(chat_id=YOUR_MANAGER_ID, photo=file_id)
    await update.message.reply_text("Спасибо! Фото получено. С вами свяжется менеджер.")

