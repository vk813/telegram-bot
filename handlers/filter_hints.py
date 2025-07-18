FILTER_HINTS = {
    "osmo_set": {
        "name": "Осмос: мембрана + 3 картриджа + постфильтр",
        "description": "Фильтр осмос состоит из мембраны и нескольких картриджей. Каждый элемент меняется по отдельному графику.",
        "lifetime": "Мембрана — 24 мес., картриджи — 3–6 мес., постфильтр — 12 мес.",
        "symptoms": "Снижение давления, привкус или запах воды.",
        "image": None,
    },
    "osmo_membrane": {
        "name": "Осмотическая мембрана",
        "description": "Главный элемент системы обратного осмоса, задерживает почти все примеси.",
        "lifetime": "24 месяца",
        "symptoms": "Падение производительности, ухудшение качества воды.",
        "image": None,
    },
    "osmo_prefilter": {
        "name": "Предфильтр",
        "description": "Очищает воду перед мембраной и продлевает её срок службы.",
        "lifetime": "3 месяца",
        "symptoms": "Помутнение воды, падение давления.",
        "image": None,
    },
    "osmo_carbon": {
        "name": "Угольный картридж",
        "description": "Удаляет хлор и органические вещества перед мембраной.",
        "lifetime": "6 месяцев",
        "symptoms": "Запах хлора или привкус в воде.",
        "image": None,
    },
    "osmo_post": {
        "name": "Постфильтр",
        "description": "Финальная очистка и коррекция вкуса воды после мембраны.",
        "lifetime": "12 месяцев",
        "symptoms": "Вкус воды стал хуже или появился запах.",
        "image": None,
    },
    "cart_uf": {
        "name": "3 картриджа (ультрафильтрация)",
        "description": "Не требует подключения к канализации, оптимально для мягкой воды и небольших кухонь.",
        "lifetime": "6 месяцев",
        "symptoms": "Снижение потока, помутнение или запах воды.",
        "image": None,
    },
    "post_ugol": {
        "name": "Пост-фильтр (угольный)",
        "description": "Финальная очистка, улучшает вкус и убирает запахи.",
        "lifetime": "6 месяцев",
        "symptoms": "Запах или привкус в воде.",
        "image": None,
    },
    "ugol": {
        "name": "Угольный",
        "description": "Устраняет хлор и органику, делает воду чище и безопаснее.",
        "lifetime": "6 месяцев",
        "symptoms": "Появление запаха хлора, ухудшение вкуса.",
        "image": None,
    },
    "mech": {
        "name": "Механический",
        "description": "Удаляет ржавчину, песок и другие видимые примеси.",
        "lifetime": "6 месяцев",
        "symptoms": "Снижение напора, большое количество взвеси.",
        "image": None,
    },
    "mineral": {
        "name": "Минерализатор",
        "description": "Возвращает воде полезные минералы, делает вкус мягче.",
        "lifetime": "6 месяцев",
        "symptoms": "Вкус воды стал плоским или металлическим.",
        "image": None,
    },
    "kuvshin": {
        "name": "Кувшинный",
        "description": "Портативное решение для быстрой фильтрации небольшого объёма воды.",
        "lifetime": "1 месяц",
        "symptoms": "Замедление фильтрации, неприятный запах.",
        "image": None,
    },
    "zag_mech": {
        "name": "Механический (загородный)",
        "description": "Предварительная очистка воды от крупных частиц для загородных систем.",
        "lifetime": "6 месяцев",
        "symptoms": "Снижение давления, большое количество осадка.",
        "image": None,
    },
    "zag_ugol": {
        "name": "Угольный (загородный)",
        "description": "Удаляет хлор и органику в загородных системах.",
        "lifetime": "6 месяцев",
        "symptoms": "Запах и вкус хлора.",
        "image": None,
    },
    "zag_obez": {
        "name": "Обезжелезиватель",
        "description": "Снижает содержание железа и марганца в воде.",
        "lifetime": "12 месяцев",
        "symptoms": "Жёлтый оттенок воды, металлический вкус.",
        "image": None,
    },
    "zag_um": {
        "name": "Умягчитель",
        "description": "Удаляет соли жёсткости и смягчает воду.",
        "lifetime": "12 месяцев",
        "symptoms": "Образование накипи, белый налёт на сантехнике.",
        "image": None,
    },
    "zag_comb": {
        "name": "Комбинированный",
        "description": "Сочетает несколько типов очистки для загородного водоснабжения.",
        "lifetime": "12 месяцев",
        "symptoms": "Ухудшение качества воды в целом.",
        "image": None,
    },
    "zag_uf": {
        "name": "УФ-лампа",
        "description": "Обеззараживает воду ультрафиолетовым излучением.",
        "lifetime": "12 месяцев",
        "symptoms": "Необходимость замены определяется снижением яркости лампы.",
        "image": None,
    },
}

from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def get_filter_info(filter_key: str):
    """Return brief description text and buttons for the filter."""
    data = FILTER_HINTS.get(filter_key)
    if not data:
        return None, None

    text = (
        f"{data['name']}\n"
        f"{data['description']}\n"
        f"Срок службы: {data['lifetime']}.\n"
        f"{data['symptoms']}"
    )

    buttons = [[InlineKeyboardButton("❓ Подробнее", callback_data=f"filter_more_{filter_key}")]]
    if data.get("image"):
        buttons.append([InlineKeyboardButton("Показать схему", callback_data=f"filter_scheme_{filter_key}")])

    return text, InlineKeyboardMarkup(buttons)

