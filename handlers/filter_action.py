from database import async_session, Filter
from sqlalchemy import select
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from utils import safe_callback_data
from telegram.ext import ConversationHandler, ContextTypes
from datetime import datetime, timezone
import logging

from constants import MAIN_LABELS, ZAGOROD_LABELS, filter_status_color

logger = logging.getLogger(__name__)

SHOW_FILTER_ACTIONS, CONFIRM_REPLACE, ENTER_NOTE = range(3)
CANCEL_BUTTON = "❌ Отмена"

def safe_handler(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await func(update, context)
        except Exception as e:
            logger.exception("Ошибка в filter_action.py: %s", e)
            msg = getattr(update, "effective_message", None)
            if msg:
                await msg.reply_text("Что-то пошло не так. Попробуйте позже или /start.")
            return ConversationHandler.END
    return wrapper


async def filter_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает действия по инлайн-кнопкам фильтра: удаление, отметка замены, добавление фото, автозаказ.
    """
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    try:
        if data.startswith("filter_delete_"):
            filter_id = int(data.replace("filter_delete_", ""))
            async with async_session() as session:
                filt = await session.get(Filter, filter_id)
                if filt and filt.user_id == user_id:
                    await session.delete(filt)
                    await session.commit()
                    await query.answer("Фильтр удалён!")
                    await query.message.delete()
                    # После удаления — если у пользователя нет фильтров, покажем инфо-сообщение
                    user_filters = await session.scalars(
                        select(Filter).where(Filter.user_id == user_id)
                    )
                    if not user_filters.first():
                        from utils import send_clean_message
                        await send_clean_message(update, context, "У вас нет фильтров. 📝 Добавьте первый!")
                else:
                    await query.answer("Ошибка удаления!", show_alert=True)
            return

        if data.startswith("filter_replaced_"):
            filter_id = int(data.replace("filter_replaced_", ""))
            async with async_session() as session:
                filt = await session.get(Filter, filter_id)
                if filt and filt.user_id == user_id:
                    if not filt.history:
                        filt.history = []
                    filt.history.append({
                        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "comment": "Пользователь отметил замену"
                    })
                    filt.replace_count = (filt.replace_count or 0) + 1
                    filt.install_date = datetime.now(timezone.utc).date()
                    await session.commit()
                    await query.answer("Отметили замену!")

                    days_left = filt.interval
                    status = filter_status_color(days_left)
                    title = filt.name or MAIN_LABELS.get(filt.type, ZAGOROD_LABELS.get(filt.type, filt.type.title()))
                    text = (
                        f"{status} <b>{title}</b>\n"
                        f"Установлен: {filt.install_date:%d.%m.%Y}\n"
                        f"Осталось: <b>{days_left} д.</b>\n"
                        f"Замен: {filt.replace_count}\n"
                    )
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                "✅ Уже заменил",
                                callback_data=safe_callback_data(f"filter_replaced_{filt.id}")
                            ),
                            InlineKeyboardButton(
                                "❌ Удалить",
                                callback_data=safe_callback_data(f"filter_delete_{filt.id}")
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "📸 Добавить фото",
                                callback_data=safe_callback_data(f"add_photo_{filt.id}")
                            ),
                            InlineKeyboardButton(
                                "✏️ Переименовать",
                                callback_data=safe_callback_data(f"rename_filter_{filt.id}")
                            )
                        ]
                    ]
                    markup = InlineKeyboardMarkup(keyboard)
                    await query.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
                else:
                    await query.answer("Ошибка!", show_alert=True)
            return
        
        if data.startswith("add_photo_"):
            filter_id = int(data.replace("add_photo_", ""))
            context.user_data["last_filter_id"] = filter_id
            await query.answer()
            await query.message.reply_text(
                "Пожалуйста, отправьте фото для этого фильтра одним сообщением или воспользуйтесь кнопкой /done для завершения."
            )
            return

        if data.startswith("autoorder_"):
            try:
                await autoorder_handler(update, context)
            except NameError:
                await query.answer("Функция автозаказа пока не реализована.", show_alert=True)
            return

    except Exception as e:
        logging.error(f"Ошибка обработки действия фильтра: {e}")
        await query.answer("Внутренняя ошибка.", show_alert=True)
    return None
