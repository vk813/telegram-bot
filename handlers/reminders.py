# handlers/reminders.py
from database import async_session, Filter
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import logging

async def send_reminders(context):
    today = datetime.now(timezone.utc).date()
    async with async_session() as session:
        result = await session.execute(select(Filter))
        filters = result.scalars().all()
        for f in filters:
            days_left = (f.install_date + timedelta(days=f.interval) - today).days
            if days_left in [15, 5, 0]:
                try:
                    await context.bot.send_message(
                        chat_id=f.user_id,
                        text=(
                            f"🔔 Напоминание!\n"
                            f"Фильтр '{f.type}' установлен {f.install_date:%d.%m.%Y}.\n"
                            f"Осталось дней: <b>{days_left}</b>.\n"
                            f"Пора задуматься о замене фильтра!"
                        ),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logging.error(f"Ошибка отправки напоминания: {e}")
