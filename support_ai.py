import requests
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

OLLAMA_API_URL = "http://localhost:11434/api/generate"  # измените если Ollama не на localhost

YOUR_MANAGER_CONTACT = "@vkup25"  # замените на свой username

# Сколько вопросов подряд разрешено задавать AI без менеджера
AI_QUESTION_LIMIT = 5

async def handle_ai_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_q_count = context.user_data.get("ai_q_count", 0)

    # Лимит по вопросам
    if user_q_count >= AI_QUESTION_LIMIT:
        await update.effective_message.reply_text(
            f"🤖 Спасибо за ваши вопросы! Чтобы получить персональную рекомендацию или расчет — напишите менеджеру {YOUR_MANAGER_CONTACT}.\n\n"
            "Если остались технические вопросы — задайте их здесь, я подскажу всё, что знаю!"
        )
        return ConversationHandler.END

    # Получаем вопрос пользователя
    if update.message and update.message.text:
        question = update.message.text.strip()
    elif update.callback_query and update.callback_query.data:
        question = update.callback_query.data.strip()
    else:
        await update.effective_message.reply_text("Пожалуйста, напишите свой вопрос текстом.")
        return ConversationHandler.END

    try:
        # Запрос к Ollama
        response = requests.post(
            OLLAMA_API_URL,
            json={"model": "llama3", "prompt": question, "stream": False},
            timeout=40
        )
        response.raise_for_status()
        answer = response.json().get("response", "Извините, сейчас нет ответа.")
    except Exception as e:
        answer = "🤖 Сейчас не могу получить ответ. Попробуйте чуть позже или напишите менеджеру."

    await update.effective_message.reply_text(answer)

    # Увеличиваем счетчик вопросов
    context.user_data["ai_q_count"] = user_q_count + 1
    if context.user_data["ai_q_count"] >= AI_QUESTION_LIMIT:
        await update.effective_message.reply_text(
            f"🔔 Если нужны индивидуальные рекомендации — свяжитесь с менеджером {YOUR_MANAGER_CONTACT}"
        )

    return ConversationHandler.END
