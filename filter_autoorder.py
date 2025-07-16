from telegram import Update
from telegram.ext import ContextTypes

async def autoorder_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    try:
        if data.startswith("autoorder_"):
            filter_id = int(data.replace("autoorder_", ""))
            async with async_session() as session:
                filt = await session.get(Filter, filter_id)
                if filt and filt.user_id == user_id:
                    # Проверяем наличие поля auto_order
                    if not hasattr(filt, "auto_order"):
                        await query.answer("Данное действие временно недоступно.", show_alert=True)
                        logging.error("Поле auto_order отсутствует в модели Filter!")
                        return

                    filt.auto_order = not bool(getattr(filt, "auto_order", False))
                    await session.commit()
                    await query.answer(
                        f"Автозаказ {'включён' if filt.auto_order else 'выключен'}!"
                    )
                    # Лучше edit_message, а не reply_text
                    await query.message.edit_text(
                        f"🔁 Автозаказ для фильтра {'включён' if filt.auto_order else 'выключен'}.",
                        parse_mode="HTML"
                    )
                else:
                    await query.answer("Ошибка!", show_alert=True)
    except Exception as e:
        logging.error(f"Ошибка в autoorder_handler: {e}")
        await query.answer("Внутренняя ошибка.", show_alert=True)
    return
