# Telegram Bot Troubleshooting

This repository uses a `.env` file or environment variables to provide the bot token (`BOT_TOKEN`).

If the bot fails to start with an `InvalidToken` error:

1. Ensure the token value from BotFather is stored **exactly** as provided without extra spaces or line breaks.
2. Replace the token in your `.env` or deployment configuration if it might be outdated. You can regenerate a token via the `/token` or `/revoke` command in BotFather.
3. Restart the bot after updating the token.
4. Check the logs for a message about polling starting. Sending `/start` should trigger a greeting.

For quick diagnostics you can run a minimal bot:

```bash
python scripts/token_check.py
```

This script starts a simple bot with one `/start` command that replies "Привет! Бот работает." and prints the user ID to the console. Use it to verify that the token is valid and the bot receives updates.

If the issue persists, verify that only one bot instance is running, that your network or proxy allows Telegram connections, and that no other service is using the same token.

