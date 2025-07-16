from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from utils import safe_callback_data
from telegram.ext import ContextTypes, ConversationHandler
import logging
from datetime import datetime, timedelta
import json
from database import async_session, Filter
from sqlalchemy import select

from constants import (
    CHOOSING_TYPE, CHOOSING_DATE, MAIN_LABELS, ZAGOROD_LABELS,
    VK_CONTACT, CTA_VARIANTS, filter_status_color, get_main_inline_keyboard, get_filters_keyboard,
    PROFILE_EDIT, PROFILE_PHONE, PROFILE_EMAIL, get_back_keyboard, FILTER_INTERVALS
)
from handlers.filter_hints import FILTER_HINTS, get_filter_info
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

# --- Декоратор для ошибок ---
def safe_handler(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await func(update, context)
        except Exception as e:
            logger.exception("Ошибка в filter.py: %s", e)
            msg = getattr(update, "effective_message", None)
            if msg:
                await msg.reply_text("Что-то пошло не так. Попробуйте позже или /start.")
            return ConversationHandler.END
    return wrapper

def parse_date(date_str):
    for fmt in ("%d.%m.%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except Exception:
            continue
    return None

CHOOSING_DATE = 10

async def filter_choose_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug(
        "filter_choose_callback called: update=%r callback_data=%r",
        update,
        getattr(update.callback_query, "data", None),
    )
    try:
        query = update.callback_query
        filter_type = query.data
        context.user_data["selected_filter_type"] = filter_type

        await query.answer()
        info_text, info_kb = get_filter_info(filter_type)
        if info_text:
            await query.message.reply_text(info_text, reply_markup=info_kb)

        await query.message.reply_text(
            f"📅 Вы выбрали: {MAIN_LABELS.get(filter_type, filter_type)}.\n",
            "Введите дату установки фильтра (например, 09.07.2025):",
        )
        return CHOOSING_DATE
    except Exception:
        logging.exception("Unhandled exception in filter_choose_callback")
        if update.callback_query:
            await update.callback_query.answer("Произошла ошибка", show_alert=True)
        return ConversationHandler.END


@safe_handler
async def handle_choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_str = update.message.text.strip()
    install_date = parse_date(date_str)
    if not install_date:
        await update.message.reply_text("❗️ Введите дату в формате ДД.ММ.ГГГГ")
        return CHOOSING_DATE

    user_id = update.effective_user.id
    filter_type = context.user_data.get("selected_filter_type")
    if not filter_type:
        await update.message.reply_text("Не удалось определить тип фильтра. Попробуйте сначала.")
        return ConversationHandler.END

    async with async_session() as session:
        filter_obj = Filter(
            user_id=user_id,
            type=filter_type,
            install_date=install_date,
            interval=FILTER_INTERVALS[filter_type],
            name=MAIN_LABELS.get(filter_type)
        )
        session.add(filter_obj)
        await session.commit()

    await update.message.reply_text(
        "✅ Фильтр добавлен! Напомню о замене вовремя.",
        reply_markup=get_main_inline_keyboard()
    )
    context.user_data.pop("selected_filter_type", None)
    return ConversationHandler.END

async def filter_hint_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data.startswith("hint_"):
        key = query.data.replace("hint_", "")
    else:
        key = query.data.replace("filter_more_", "")
    data = FILTER_HINTS.get(key)

    if not data:
        await query.answer("Нет описания для этого фильтра.", show_alert=True)
        return

    text = (
        f"<b>{data['name']}</b>\n"
        f"{data['description']}\n\n"
        f"<b>Срок службы:</b> {data['lifetime']}\n"
        f"<b>Когда менять:</b> {data['symptoms']}"
    )

    if data.get("image"):
        await query.message.reply_photo(
            data["image"], caption=text, parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
        await query.answer()
    elif len(text) < 180:
        await query.answer(text=text, show_alert=True)
    else:
        await query.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
        await query.answer()


async def filter_scheme_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send filter scheme/photo if available."""
    query = update.callback_query
    key = query.data.replace("filter_scheme_", "")
    data = FILTER_HINTS.get(key)

    if not data or not data.get("image"):
        await query.answer("Схема недоступна", show_alert=True)
        return

    await query.message.reply_photo(open(data["image"], "rb"))
    await query.answer()


async def show_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список фильтров пользователя с кнопками действий."""
    user_id = update.effective_user.id if update.effective_user else (
        update.callback_query.from_user.id if getattr(update, "callback_query", None) else None
    )
    if not user_id:
        logger.error("Не удалось определить user_id.")
        await update.effective_message.reply_text("Ошибка: не удалось определить пользователя.")
        return ConversationHandler.END

    try:
        async with async_session() as session:
            result = await session.scalars(
                select(Filter).where(Filter.user_id == user_id).order_by(Filter.install_date.desc())
            )
            filters = result.all()
    except Exception as e:
        logger.error(f"Ошибка получения фильтров (user_id={user_id}): {e}")
        await update.effective_message.reply_text("Ошибка загрузки фильтров.")
        return ConversationHandler.END

    if not filters:
        await update.effective_message.reply_text(
            "У вас нет фильтров. 📝 Добавьте первый!",
            reply_markup=get_main_inline_keyboard()
        )
        return ConversationHandler.END

    today = datetime.now().date()
    await update.effective_message.reply_text("Ваши фильтры:")

    for f in filters:
        days_left = (f.install_date + timedelta(days=f.interval) - today).days
        status = filter_status_color(days_left)
        title = (
            f.name or
            MAIN_LABELS.get(f.type) or
            ZAGOROD_LABELS.get(f.type) or
            f.type.title()
        )

        text = (
            f"{status} <b>{title}</b>\n"
            f"Установлен: {f.install_date:%d.%m.%Y}\n"
            f"Осталось: <b>{days_left} д.</b>\n"
            f"Замен: {getattr(f, 'replace_count', 0)}\n"
        )

        # ----------- КНОПКИ ДЕЙСТВИЙ -----------
        keyboard = [
            [
                InlineKeyboardButton("✅ Уже заменил", callback_data=safe_callback_data(f"filter_replaced_{f.id}")),
                InlineKeyboardButton("❌ Удалить", callback_data=safe_callback_data(f"filter_delete_{f.id}"))
            ],
            [
                InlineKeyboardButton("ℹ️ Описание", callback_data=safe_callback_data(f"hint_{f.type}")),
                InlineKeyboardButton("✏️ Переименовать", callback_data=safe_callback_data(f"rename_filter_{f.id}"))
            ],
            [
                InlineKeyboardButton("📸 Добавить фото", callback_data=safe_callback_data(f"add_photo_{f.id}"))
            ]
        ]

        # ----------- ФОТО -----------
        photos_list = []
        photos = getattr(f, "photos", None)
        if photos:
            if isinstance(photos, str):
                try:
                    photos_list = json.loads(photos)
                except Exception as ex:
                    logger.warning(f"Не удалось распарсить photos у фильтра {f.id}: {ex}")
                    photos_list = []
            elif isinstance(photos, list):
                photos_list = photos
        if len(photos_list) > 0:
            keyboard.append([
                InlineKeyboardButton("👁 Смотреть фото", callback_data=safe_callback_data(f"view_photos_{f.id}")),
                InlineKeyboardButton("🗑 Удалить фото", callback_data=safe_callback_data(f"del_photo_{f.id}"))
            ])
            text += f"\n📸 Есть фото: {len(photos_list)}"

        markup = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text(
            text, parse_mode="HTML", reply_markup=markup
        )
        context.user_data["last_filter_id"] = f.id

    await update.effective_message.reply_text(
        "Выберите дальнейшее действие:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 В меню", callback_data=safe_callback_data("back_to_menu"))]
        ])
    )
    return ConversationHandler.END
