import os
import logging
from telegram import InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from handlers.common import start

from database import async_session, Filter

PHOTO_WAIT = 100
MAX_PHOTOS = 10
PHOTO_DIR = "photos"
if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR, exist_ok=True)
if not os.access(PHOTO_DIR, os.W_OK):
    raise Exception(f"Нет прав на запись в папку {PHOTO_DIR}")

def ensure_list(photos):
    """Привести поле photos к списку (list), даже если это строка или None."""
    if isinstance(photos, list):
        return photos
    if not photos:
        return []
    import json
    try:
        return json.loads(photos)
    except Exception:
        return []

async def add_photo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        filter_id = int(query.data.replace("add_photo_", ""))
    except ValueError:
        await query.edit_message_text("Ошибка: неверный формат ID фильтра.")
        return ConversationHandler.END
    context.user_data["photo_filter_id"] = filter_id
    await query.edit_message_text(
        "Пожалуйста, отправьте одно или несколько фото для этого фильтра. По окончании пришлите /done."
    )
    return PHOTO_WAIT

async def wait_for_filter_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = getattr(update, "message", None) or getattr(update, "callback_query", None)
    if msg:
        await msg.reply_text("Ожидание фото для фильтра...")
    return PHOTO_WAIT

async def add_filter_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filter_id = context.user_data.get("photo_filter_id")
    if not filter_id:
        await update.message.reply_text("Ошибка: не выбран фильтр. Начните заново.")
        return PHOTO_WAIT

    if not update.message.photo:
        await update.message.reply_text("Это не фото. Пожалуйста, отправьте фотографию фильтра.")
        return PHOTO_WAIT

    photo = update.message.photo[-1]
    try:
        file = await photo.get_file()
        filename = f"{update.effective_user.id}_{filter_id}_{photo.file_unique_id}.jpg"
        path = os.path.join(PHOTO_DIR, filename)
        await file.download_to_drive(custom_path=path)
    except Exception as e:
        logging.error(f"Ошибка при скачивании фото: {e}")
        await update.message.reply_text(
            "Ошибка при загрузке фото. Попробуйте ещё раз или напишите в поддержку @660442813"
        )
        return PHOTO_WAIT

    try:
        async with async_session() as session:
            filter_obj = await session.get(Filter, filter_id)
            if not filter_obj or filter_obj.user_id != update.effective_user.id:
                await update.message.reply_text("Фильтр не найден или принадлежит другому пользователю.")
                return PHOTO_WAIT

            # ГАРАНТИЯ, ЧТО ВСЕГДА СПИСОК
            filter_obj.photos = ensure_list(filter_obj.photos)

            photo_count = len(filter_obj.photos)
            if photo_count >= MAX_PHOTOS:
                await update.message.reply_text(
                    f"Можно добавить не более {MAX_PHOTOS} фото к одному фильтру.\n"
                    f"Сейчас уже загружено: {photo_count}."
                )
                return PHOTO_WAIT

            filter_obj.photos.append(os.path.join(PHOTO_DIR, filename))
            await session.commit()

        await update.message.reply_text(
            f"Фото добавлено! Можете отправить ещё (загружено: {photo_count + 1}/{MAX_PHOTOS}) или завершить командой /done."
        )
        ADMIN_ID = int(os.getenv("ADMIN_CHAT_ID", "660442813"))
        try:
            with open(path, "rb") as photo_file:
                await context.bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=photo_file,
                    caption=f"Новое фото для фильтра {filter_id} от пользователя {update.effective_user.id}"
                )
        except Exception as e:
            logging.error(f"Ошибка отправки фото админу: {e}")
            await update.message.reply_text("Внимание: фото не удалось отправить менеджеру. Мы уже решаем проблему.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении фото в БД: {e}")
        await update.message.reply_text(
            "Ошибка при сохранении фото. Попробуйте ещё раз или обратитесь в поддержку @660442813"
        )
    return PHOTO_WAIT

async def save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await add_filter_photo(update, context)

async def finish_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Фото сохранены. Возвращаемся в фильтры.")
    context.user_data.pop("photo_filter_id", None)
    from handlers.filter import show_filters
    return await show_filters(update, context)

async def show_filter_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Filter).where(Filter.user_id == user_id))
        filters = result.scalars().all()

    photo_entries = []
    for f in filters:
        photos = ensure_list(f.photos)
        for idx, p in enumerate(photos):
            photo_entries.append({
                "photo": p,
                "caption": f"Фильтр: {getattr(f, 'name', '') or getattr(f, 'type', '')} (#{f.id})\nФото {idx+1} из {len(photos)}"
            })

    if not photo_entries:
        await (update.message or update.callback_query.message).reply_text("У вас пока нет загруженных фото фильтров.")
        return

    context.user_data["my_photos"] = photo_entries
    context.user_data["my_photo_idx"] = 0

    await send_current_photo(update, context)

async def send_current_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data.get("my_photo_idx", 0)
    photos = context.user_data.get("my_photos", [])
    if not photos:
        msg = (getattr(update, "message", None) or getattr(update, "callback_query", None)).message
        await msg.reply_text("Фото не найдены.")
        return

    entry = photos[idx]
    keyboard = []
    if idx > 0:
        keyboard.append(InlineKeyboardButton("⬅️ Назад", callback_data="photo_prev"))
    if idx < len(photos) - 1:
        keyboard.append(InlineKeyboardButton("➡️ Далее", callback_data="photo_next"))

    msg_obj = getattr(update, "message", None)
    callback_query = getattr(update, "callback_query", None)

    if not os.path.exists(entry["photo"]):
        msg = msg_obj or callback_query.message
        await msg.reply_text("Фото не найдено на сервере.")
        return

    if callback_query:
        try:
            with open(entry["photo"], "rb") as img:
                await callback_query.message.edit_media(
                    media=InputMediaPhoto(img, caption=entry["caption"]),
                    reply_markup=InlineKeyboardMarkup([keyboard]) if keyboard else None
                )
        except Exception as e:
            logging.exception("Ошибка edit_media: %s", e)
            await callback_query.message.reply_text("Ошибка показа фото. Сообщите в поддержку.")
    else:
        try:
            with open(entry["photo"], "rb") as img:
                await msg_obj.reply_photo(
                    photo=img,
                    caption=entry["caption"],
                    reply_markup=InlineKeyboardMarkup([keyboard]) if keyboard else None
                )
        except Exception as e:
            logging.exception("Ошибка reply_photo: %s", e)
            await msg_obj.reply_text("Ошибка показа фото. Сообщите в поддержку.")

async def view_photos_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    query = update.callback_query
    filter_id = int(query.data.replace("view_photos_", ""))
    async with async_session() as session:
        filter_obj = await session.get(Filter, filter_id)
        if not filter_obj or filter_obj.user_id != update.effective_user.id:
            await query.message.reply_text("Фильтр не найден или принадлежит другому пользователю.")
            return
        photos = ensure_list(filter_obj.photos)
        if not photos:
            await query.message.reply_text("Нет фото для этого фильтра.")
            return

        context.user_data["my_photos"] = [
            {"photo": p, "caption": f"Фильтр #{filter_id} — фото {i+1} из {len(photos)}"} for i, p in enumerate(photos)
        ]
        context.user_data["my_photo_idx"] = 0
        await send_current_photo(update, context)

# ==========================
# УДАЛЕНИЕ ФОТО ПО КНОПКЕ
# ==========================

async def delete_filter_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    filter_id = int(query.data.replace("del_photo_", ""))

    async with async_session() as session:
        filter_obj = await session.get(Filter, filter_id)
        photos = ensure_list(filter_obj.photos)
        if not photos:
            await query.message.reply_text("Нет фото для этого фильтра.")
            return

        context.user_data["del_photos"] = photos
        context.user_data["del_photo_idx"] = 0
        context.user_data["del_photo_filter_id"] = filter_id

        await show_delete_photo(update, context)

async def show_delete_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data.get("del_photo_idx", 0)
    photos = context.user_data.get("del_photos", [])
    filter_id = context.user_data.get("del_photo_filter_id")

    if not photos:
        await update.callback_query.message.reply_text("Все фото удалены.")
        from handlers.filter import show_filters
        return await show_filters(update, context)

    keyboard = []
    row = []
    if idx > 0:
        row.append(InlineKeyboardButton("⬅️ Назад", callback_data="del_photo_prev"))
    if idx < len(photos) - 1:
        row.append(InlineKeyboardButton("➡️ Далее", callback_data="del_photo_next"))
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🗑 Удалить это фото", callback_data="del_photo_confirm")])
    keyboard.append([InlineKeyboardButton("🔙 К фильтру", callback_data=f"view_photos_{filter_id}")])

    photo_path = photos[idx]
    if not os.path.exists(photo_path):
        await update.callback_query.message.reply_text("Фото не найдено на сервере.")
        return

    with open(photo_path, "rb") as img:
        await update.callback_query.message.reply_photo(
            photo=img,
            caption=f"Фото {idx+1} из {len(photos)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def del_photo_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    idx = context.user_data.get("del_photo_idx", 0)
    photos = context.user_data.get("del_photos", [])

    if query.data == "del_photo_next" and idx < len(photos) - 1:
        idx += 1
    elif query.data == "del_photo_prev" and idx > 0:
        idx -= 1
    context.user_data["del_photo_idx"] = idx
    await show_delete_photo(update, context)

async def del_photo_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = context.user_data.get("del_photo_idx", 0)
    photos = context.user_data.get("del_photos", [])
    filter_id = context.user_data.get("del_photo_filter_id")

    if not photos or filter_id is None:
        await query.message.reply_text("Нет выбранного фото для удаления.")
        return

    photo_path = photos[idx]

    try:
        if os.path.exists(photo_path):
            os.remove(photo_path)
    except Exception as e:
        logging.error(f"Ошибка удаления файла: {e}")

    async with async_session() as session:
        filter_obj = await session.get(Filter, filter_id)
        if not filter_obj or filter_obj.user_id != update.effective_user.id:
            await query.message.reply_text("Фильтр не найден или принадлежит другому пользователю.")
            return
        db_photos = ensure_list(filter_obj.photos)
        if photo_path in db_photos:
            db_photos.remove(photo_path)
        filter_obj.photos = db_photos  # <-- всегда list!
        await session.commit()

    photos.pop(idx)
    if idx >= len(photos) and idx > 0:
        idx -= 1
    context.user_data["del_photo_idx"] = idx
    context.user_data["del_photos"] = photos

    if not photos:
        await query.message.reply_text("Фото удалено. Фото больше не осталось.")
        from handlers.filter import show_filters
        return await show_filters(update, context)

    await show_delete_photo(update, context)

async def photo_pagination_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    idx = context.user_data.get("my_photo_idx", 0)
    photos = context.user_data.get("my_photos", [])

    if query.data == "photo_next" and idx < len(photos) - 1:
        idx += 1
    elif query.data == "photo_prev" and idx > 0:
        idx -= 1
    context.user_data["my_photo_idx"] = idx

    entry = photos[idx]
    keyboard = []
    if idx > 0:
        keyboard.append(InlineKeyboardButton("⬅️ Назад", callback_data="photo_prev"))
    if idx < len(photos) - 1:
        keyboard.append(InlineKeyboardButton("➡️ Далее", callback_data="photo_next"))

    with open(entry["photo"], "rb") as img:
        await query.message.edit_media(
            media=InputMediaPhoto(img, caption=entry["caption"]),
            reply_markup=InlineKeyboardMarkup([keyboard]) if keyboard else None
        )
    await query.answer()

add_filter_photo_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_photo_start, pattern="^add_photo_")],
    states={
        PHOTO_WAIT: [
            MessageHandler(filters.PHOTO, save_photo),
            CommandHandler("done", finish_photo),
        ]
    },
    fallbacks=[
        CommandHandler("done", finish_photo)
    ],
    allow_reentry=True
)
