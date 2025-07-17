import calendar
import random
import logging
from sqlalchemy import select
from telegram.error import BadRequest
from utils import send_clean_message

from datetime import datetime, timezone, date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CallbackQueryHandler, ContextTypes, CommandHandler
)
from constants import (MONTH_NAMES, WEEKDAYS, CHOOSING_TYPE, CHOOSING_DATE,
                       MAIN_LABELS, ZAGOROD_LABELS,
                       FILTER_INTERVALS, SUCCESS_MESSAGES, PROFILE_EDIT, PROFILE_PHONE, PROFILE_EMAIL, REAL_TYPE_MAPPING, get_main_inline_keyboard)
from database import async_session, Filter


CONFIRM_FILTER = 10301

def build_calendar(year=None, month=None, show_today=True):
    now = datetime.now(timezone.utc)
    if year is None: year = now.year
    if month is None: month = now.month

    markup = [
        [InlineKeyboardButton(f"{MONTH_NAMES[month-1]} {year}", callback_data="calendar_ignore")],
        [InlineKeyboardButton(day, callback_data="calendar_ignore") for day in WEEKDAYS]
    ]
    for week in calendar.monthcalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="calendar_ignore"))
            else:
                row.append(InlineKeyboardButton(str(day), callback_data=f"calendar_date_{year}_{month}_{day}"))
        markup.append(row)

    nav_row = [
        InlineKeyboardButton("◀️", callback_data=f"calendar_prev_{year}_{month}"),
        InlineKeyboardButton("❌ Отмена", callback_data="calendar_cancel"),
        InlineKeyboardButton("▶️", callback_data=f"calendar_next_{year}_{month}")
    ]
    if show_today:
        today = datetime.now(timezone.utc).date()
        nav_row.insert(1, InlineKeyboardButton("📅 Сегодня", callback_data=f"calendar_today_{today.year}_{today.month}_{today.day}"))
    markup.append(nav_row)

    return InlineKeyboardMarkup(markup)

def get_progress_bar(current: int, total: int) -> str:
    """
    Возвращает текстовый прогресс-бар: ●○○ (2 из 3) для Telegram.
    """
    full = "●"
    empty = "○"
    parts = [full if i < current else empty for i in range(total)]
    return f"{''.join(parts)}  Шаг {current} из {total}"

def parse_calendar_callback(data: str):
    try:
        if data.startswith("calendar_date_"):
            _, _, year, month, day = data.split("_")
            return "date", (int(year), int(month), int(day))
        if data.startswith("calendar_today_"):
            _, _, year, month, day = data.split("_")
            return "date", (int(year), int(month), int(day))
        if data.startswith("calendar_prev_"):
            _, _, year, month = data.split("_")
            return "prev", (int(year), int(month))
        if data.startswith("calendar_next_"):
            _, _, year, month = data.split("_")
            return "next", (int(year), int(month))
    except Exception as e:
        logging.warning(f"Некорректный callback календаря: {data}")
    return "ignore", ()


async def start_add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт регистрации фильтра."""
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("Квартирные фильтры", callback_data="choose_flat")],
        [InlineKeyboardButton("Загородные фильтры", callback_data="choose_zagorod")],
        [InlineKeyboardButton("Назад", callback_data="back_to_menu")]
    ]
    await update.callback_query.message.reply_text(
        f"{get_progress_bar(1, 3)}\nВыберите категорию фильтра:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_TYPE


async def choose_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data
    context.user_data["filter_category"] = "flat" if category == "choose_flat" else "zagorod"
    filters = MAIN_LABELS if category == "choose_flat" else ZAGOROD_LABELS
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"filter_{key}")]
        for key, label in filters.items()
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")])
    await query.edit_message_text(
        f"{get_progress_bar(2, 3)}\nВыберите фильтр:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_DATE


async def choose_filter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    filter_key = query.data.replace("filter_", "")
    real_type = REAL_TYPE_MAPPING.get(filter_key)
    if not real_type:
        await query.answer("Неизвестный фильтр.", show_alert=True)
        return CHOOSING_TYPE
    context.user_data["chosen_filter"] = filter_key
    context.user_data["real_filter_type"] = real_type
    await query.edit_message_text(
        f"{get_progress_bar(3, 3)}\nВыберите дату установки фильтра:",
        reply_markup=build_calendar()
    )
    return CHOOSING_DATE



async def cancel_calendar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Операция отменена.",
        reply_markup=get_main_inline_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END


async def calendar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, payload = parse_calendar_callback(query.data)
    if action == "prev":
        year, month = payload
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
        await query.edit_message_reply_markup(reply_markup=build_calendar(year, month))
        return CHOOSING_DATE

    elif action == "next":
        year, month = payload
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
        await query.edit_message_reply_markup(reply_markup=build_calendar(year, month))
        return CHOOSING_DATE
    
    elif action == "date":
        year, month, day = payload
        chosen_date = date(year, month, day)
        today = datetime.now(timezone.utc).date()
        if chosen_date > today:
            await query.answer("Дата установки не может быть в будущем.", show_alert=True)
            await query.edit_message_reply_markup(reply_markup=build_calendar(year, month))
            return CHOOSING_DATE

        context.user_data['install_date'] = chosen_date
        filter_key = context.user_data.get("chosen_filter", "")
        real_type = context.user_data.get("real_filter_type", filter_key)
        filter_label = MAIN_LABELS.get(filter_key) or ZAGOROD_LABELS.get(filter_key) or filter_key

        text = (
            f"Вы выбрали:\n"
            f"• Тип фильтра: {filter_label}\n"
            f"• Дата установки: {chosen_date:%d.%m.%Y}\n\n"
            f"<b>После сохранения фильтр появится в разделе «Мои фильтры».</b>\n\n"
            f"Всё верно?"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Сохранить", callback_data="filter_confirm_save")],
            [InlineKeyboardButton("⬅️ Назад к дате", callback_data="filter_back_to_date")],
            [InlineKeyboardButton("❌ Отмена", callback_data="calendar_cancel")]
        ])
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
        return CONFIRM_FILTER

async def filter_confirm_save_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chosen_date = context.user_data.get('install_date')
    filter_key = context.user_data.get("chosen_filter", "")
    real_type = context.user_data.get("real_filter_type", filter_key)
    filter_label = MAIN_LABELS.get(filter_key) or ZAGOROD_LABELS.get(filter_key) or filter_key
    interval = FILTER_INTERVALS.get(filter_key, 90)
    try:
        async with async_session() as session:
            exists = await session.scalar(
                select(Filter).where(
                    (Filter.user_id == user_id) &
                    (Filter.type == real_type) &
                    (Filter.install_date == chosen_date)
                )
            )
            if exists:
                await query.edit_message_text(
                    "❗ Такой фильтр уже есть. Выберите другую дату или фильтр.",
                    reply_markup=build_calendar(chosen_date.year, chosen_date.month)
                )
                return CHOOSING_DATE
            f = Filter(
                user_id=user_id,
                type=real_type,
                install_date=chosen_date,
                interval=interval,
                next_reminder_date=chosen_date + timedelta(days=interval - 15)
            )
            session.add(f)
            await session.commit()
    except Exception as e:
        logging.error(f"Ошибка сохранения фильтра: {e}")
        await query.edit_message_text("Ошибка сохранения фильтра.")
        return ConversationHandler.END

    await query.edit_message_text(
        f"{random.choice(SUCCESS_MESSAGES)}\n\n"
        f"Тип фильтра: {filter_label}\n"
        f"Дата установки: {chosen_date:%d.%m.%Y}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")]])
    )
    context.user_data.clear()
    return ConversationHandler.END

async def filter_back_to_date_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chosen_date = context.user_data.get('install_date')
    month = chosen_date.month if chosen_date else datetime.now(timezone.utc).month
    year = chosen_date.year if chosen_date else datetime.now(timezone.utc).year
    await query.edit_message_text(
        f"{get_progress_bar(3, 3)}\nВыберите дату установки фильтра:",
        reply_markup=build_calendar(year, month)
    )
    return CHOOSING_DATE


async def back_to_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.effective_message.reply_text(
        "Главное меню:",
        reply_markup=get_main_inline_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END

reg_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_add_filter, pattern="^register$")],
    states={
        CHOOSING_TYPE: [CallbackQueryHandler(choose_category_handler, pattern="^choose_")],
        CHOOSING_DATE: [
            CallbackQueryHandler(choose_filter_handler, pattern="^filter_"),
            CallbackQueryHandler(calendar_handler, pattern="^calendar_"),
            CallbackQueryHandler(cancel_calendar_handler, pattern="^calendar_cancel$")
        ],
        CONFIRM_FILTER: [
            CallbackQueryHandler(filter_confirm_save_handler, pattern="^filter_confirm_save$"),
            CallbackQueryHandler(filter_back_to_date_handler, pattern="^filter_back_to_date$"),
            CallbackQueryHandler(cancel_calendar_handler, pattern="^calendar_cancel$")
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_menu_callback, pattern="^back_to_menu$"),
        CallbackQueryHandler(cancel_calendar_handler, pattern="^calendar_cancel$"),
],
)
