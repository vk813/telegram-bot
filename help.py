from telegram import Update
from telegram.ext import ContextTypes
from utils import send_clean_message


# 🔐 Твой Telegram ID — для отправки уведомлений
ADMIN_CHAT_ID = 660442813

async def ai_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user

    # Отправка тебе уведомления
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            "❗ Пользователь не знает, какой фильтр выбрать:\n"
            f"👤 <b>{user.full_name}</b> (@{user.username})\n"
            f"🆔 ID: <code>{user.id}</code>"
        ),
        parse_mode="HTML"
    )

    # Ответ пользователю
    await query.edit_message_text(
        "Спасибо! Мы уже передали информацию специалисту.\n"
        "Он свяжется с вами в Telegram в ближайшее время. 🙌"
    )
