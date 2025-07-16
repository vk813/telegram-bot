import aiohttp
import os

YANDEX_GPT_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

async def ask_yandex_gpt(prompt: str) -> str:
    iam_token = os.getenv("YANDEX_IAM_TOKEN")
    folder_id = os.getenv("YANDEX_FOLDER_ID")

    headers = {
        "Authorization": f"Bearer {iam_token}",
        "Content-Type": "application/json"
    }

    json_data = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",  # или yandexgpt/latest
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 1000
        },
        "messages": [
            {"role": "user", "text": prompt}
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(YANDEX_GPT_API_URL, headers=headers, json=json_data) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["result"]["alternatives"][0]["message"]["text"]
            else:
                err = await resp.text()
                raise Exception(f"YandexGPT API error: {resp.status} - {err}")

