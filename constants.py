from telegram import InlineKeyboardButton, InlineKeyboardMarkup  
VK_CONTACT = ""


ADMIN_CHAT_ID = 660442813
ADMIN_PHONE_NUMBER = "+79213319791"


MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
])

MONTH_NAMES = [
    "Январь", "Февраль", "Март", "Апрель",
    "Май", "Июнь", "Июль", "Август",
    "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]
WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

FILTER_INTERVALS = {
    # Квартира
    "osmo_membrane": 720,    # 24 месяца
    "osmo_prefilter": 90,     # 3 месяца
    "osmo_carbon": 180,       # 6 месяцев
    "osmo_post": 365,         # 12 месяцев
    "cart_uf": 180,        # 6 месяцев
    "post_ugol": 180,      # 6 месяцев
    "ugol": 180,           # 6 месяцев
    "mech": 180,           # 6 месяцев
    "mineral": 180,        # 6 месяцев
    "kuvshin": 30,         # 1 месяц

    # Загород
    "zag_mech": 180,       # 6 месяцев
    "zag_ugol": 180,       # 6 месяцев
    "zag_obez": 365,       # 12 месяцев
    "zag_um": 365,         # 12 месяцев
    "zag_comb": 365,       # 12 месяцев
    "zag_uf": 365,         # 12 месяцев
}

# Короткие идентификаторы для callback_data
MAIN_LABELS = {
    "osmo_set": "💧 Осмос: мембрана + 3 картриджа + постфильтр",
    "cart_uf": "💧 3 картриджа (ультрафильтрация)",
    "post_ugol": "🌑 Пост-фильтр (угольный)",
    "ugol": "🌑 Угольный",
    "mech": "🌀 Механический",
    "mineral": "🧬 Минерализатор",
    "kuvshin": "🥤 Кувшинный",
}

OSMO_SET_MODULES = [
    "osmo_membrane",
    "osmo_prefilter",
    "osmo_carbon",
    "osmo_post",
]


FILTER_HINTS = {
    "osmo_set": "💧 Фильтр осмос: 5 элементов, меняются по-разному. Бот напомнит про каждый модуль отдельно!",
    "cart_uf": "💧 3 картриджа (ультрафильтрация) — не требует подключения к канализации, оптимально для мягкой воды и небольших кухонь.",
    "post_ugol": "🌑 Пост-фильтр (угольный) — финальная очистка, улучшает вкус и убирает запахи.",
    "ugol": "🌑 Угольный — устраняет хлор и органику, делает воду чище и безопаснее.",
    "mech": "🌀 Механический — удаляет ржавчину, песок и другие видимые примеси.",
    "mineral": "🧬 Минерализатор — возвращает воде полезные минералы, делает вкус мягче.",
    "kuvshin": "🥤 Кувшинный — портативное решение для быстрой фильтрации небольшого объема воды.",
}

# Подробные описания фильтров и советы по уходу
FILTER_DETAILS = {
    "osmo_set": (
        "Осмос — система из мембраны и картриджей. "
        "Промывайте колбы при каждой замене и следите за давлением. "
        "Подробнее: https://example.com/faq/osmo"
    ),
    "cart_uf": (
        "Три картриджа ультрафильтрации. Меняйте по очереди и не допускайте "
        "застоя воды. FAQ: https://example.com/faq/uf"
    ),
    "post_ugol": (
        "Угольный пост‑фильтр улучшает вкус воды. "
        "Меняйте раз в 6 месяцев и не оставляйте без протока более недели. "
        "Читать FAQ: https://example.com/faq/post"
    ),
    "ugol": (
        "Угольный картридж удаляет хлор и запахи. "
        "Рекомендуется промывать систему перед заменой. "
        "Подробнее: https://example.com/faq/ugol"
    ),
    "mech": (
        "Механический фильтр задерживает песок и ржавчину. "
        "При сильном загрязнении промывайте колбу. "
        "FAQ: https://example.com/faq/mech"
    ),
    "mineral": (
        "Минерализатор обогащает воду солями. "
        "Соблюдайте сроки замены, чтобы сохранить вкус. "
        "Читать больше: https://example.com/faq/mineral"
    ),
    "kuvshin": (
        "Кувшинный фильтр удобен в дороге. "
        "Меняйте картридж раз в месяц и держите кувшин в чистоте. "
        "Подробнее: https://example.com/faq/kuvshin"
    ),
    "zag_mech": (
        "Загородный механический фильтр защищает систему от песка. "
        "Промывайте отстойник по мере загрязнения. "
        "FAQ: https://example.com/faq/zag_mech"
    ),
    "zag_ugol": (
        "Загородный угольный фильтр улучшает вкус воды в доме. "
        "Меняйте своевременно и следите за качеством входной воды. "
        "Подробнее: https://example.com/faq/zag_ugol"
    ),
    "zag_obez": (
        "Обезжелезиватель устраняет избыток железа. "
        "Регулярно обслуживайте систему промывкой. "
        "FAQ: https://example.com/faq/zag_obez"
    ),
    "zag_um": (
        "Умягчитель борется с накипью. "
        "Следите за уровнем соли и проводите регенерацию. "
        "Читать больше: https://example.com/faq/zag_um"
    ),
    "zag_comb": (
        "Комбинированный фильтр объединяет несколько ступеней. "
        "Соблюдайте график обслуживания каждой из них. "
        "Подробнее: https://example.com/faq/zag_comb"
    ),
    "zag_uf": (
        "УФ‑лампа обеззараживает воду. "
        "Меняйте лампу согласно паспорту и протирайте колбу. "
        "FAQ: https://example.com/faq/zag_uf"
    ),
}


ZAGOROD_LABELS = {
    "zag_mech": "🌀 Механический (загородный)",
    "zag_ugol": "🌑 Угольный (загородный)",
    "zag_obez": "💧 Обезжелезиватель",
    "zag_um": "💧 Умягчитель",
    "zag_comb": "💧 Комбинированный",
    "zag_uf": "☀️ УФ-лампа",
}

REAL_TYPE_MAPPING = {
    # Квартира
    "osmo_set": "Осмос: мембрана + 3 картриджа + постфильтр",
    "cart_uf": "3 картриджа (ультрафильтрация)",
    "post_ugol": "пост-фильтр (угольный)",
    "ugol": "угольный",
    "mech": "механический",
    "mineral": "минерализатор",
    "kuvshin": "кувшинный",
    # Загород
    "zag_mech": "загородный_механический",
    "zag_ugol": "загородный_угольный",
    "zag_obez": "загородный_обезжелезиватель",
    "zag_um": "загородный_умягчитель",
    "zag_comb": "загородный_комбинированный",
    "zag_uf": "загородный_уф-лампа",
}

WELCOME_EMOJIS = ["👋", "😊", "💧", "🚰", "🤖", "🫧"]
SUCCESS_MESSAGES = [
    "🎉 Готово! Фильтр зарегистрирован.",
    "✅ Фильтр добавлен! Спасибо, что следите за чистотой воды.",
    "🚀 Отлично! Теперь фильтр под контролем.",
    "🔔 Я запомнил ваш фильтр. Напомню о замене вовремя!"
]
CTA_VARIANTS = [
    "💧 Заказать фильтры",
    "🚚 Оформить доставку фильтра",
    "🛒 Купить фильтр со скидкой"
]

CHOOSING_DATE = 0
CHOOSING_TYPE = 1

PROFILE_EDIT = 0
PROFILE_PHONE = 1
PROFILE_EMAIL = 2

# ------------------ КНОПКИ и ПОДСКАЗКИ ------------------

BACK_BUTTON = "⬅️ Назад"
CANCEL_BUTTON = "❌ Отмена"
MENU_BUTTON = "🏠 Главное меню"
SUBSCRIBE_BUTTON = "📝 Подписка"
HELP_BUTTON = "❓ Помощь"


def get_main_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить фильтр", callback_data="register")],
        [InlineKeyboardButton("📋 Мои фильтры", callback_data="show")],
        [InlineKeyboardButton("🔍 Узнать, какой у меня фильтр", callback_data="know_filter")],  
        [InlineKeyboardButton("📝 Подписка", callback_data="subscriptions")],
        [InlineKeyboardButton("❓ Не знаю что выбрать", callback_data="ai_help")],
    ])


def get_filters_keyboard():
    keyboard = []
    for key, label in MAIN_LABELS.items():
        row = [
            InlineKeyboardButton(label, callback_data=key),
            InlineKeyboardButton("ℹ️", callback_data=f"hint_{key}")
        ]
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🤖 Не знаю, что выбрать", callback_data="ai_help")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="go_back")])
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой Назад."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(BACK_BUTTON, callback_data="go_back")]
    ])

def get_back_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопками Назад и Отмена."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(BACK_BUTTON, callback_data="go_back")],
        [InlineKeyboardButton(CANCEL_BUTTON, callback_data="cancel")]
    ])

def get_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата в главное меню."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(MENU_BUTTON, callback_data="main_menu")]
    ])

def get_menu_markup() -> InlineKeyboardMarkup:
    """Дублирующая клавиатура главного меню (можно удалить за неиспользованием)."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ])

# ------------------ ЧЕЛОВЕЧНЫЕ ПОДСКАЗКИ ------------------

HUMAN_HINTS = {
    "filter_choose": "👋 Пожалуйста, выберите фильтр из списка ниже. Если не нашли свой — жмите 'Назад' или спросите в разделе 'Помощь'.",
    "filter_install_date": "📅 Введите дату установки фильтра. Если ошиблись — можно вернуться назад или отменить.",
    "subscription_choose": "📝 Выберите подходящую подписку. Подробнее о каждой — в описании. Не определились? Жмите 'Назад' или спросите поддержку.",
    "profile_edit": "📝 Измените нужные данные профиля. Можно вернуться назад или отменить действие.",
    "confirmation": "✅ Всё верно? Если нет — нажмите 'Назад' и исправьте, либо 'Отмена' для отмены.",
    "default": "ℹ️ Если что-то непонятно — используйте кнопки 'Назад' или 'Главное меню'. Мы всегда готовы помочь!"
}

CANCEL_TEXT = "❌ Действие отменено. Чем ещё можем помочь?"
BACK_TEXT = "⬅️ Вы вернулись к предыдущему шагу."

# ------------------ УТИЛИТЫ ------------------

def filter_status_color(days: int) -> str:
    """Вернуть смайлик статуса фильтра по числу дней до замены."""
    if days > 10:
        return "🟢"
    if days > 0:
        return "🟡"
    return "🔴"
