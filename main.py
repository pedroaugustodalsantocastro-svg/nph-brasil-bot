import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 ENTRAR NO VIP", callback_data="entrar_vip")]
    ]

    await update.message.reply_text(
        "🔥 Bem-vindo ao NPH_BRASIL VIP!\n\n"
        "💎 Acesso ao conteúdo VIP\n"
        "💰 Valor: R$ 9,90\n\n"
        "👇 Clique no botão abaixo:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def entrar_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "💳 Vamos realizar seu pagamento!\n\n"
        "💰 Valor: R$ 9,90\n\n"
        "⌛ Aguarde enquanto preparamos o pagamento."
    )


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        CallbackQueryHandler(entrar_vip, pattern="^entrar_vip$")
    )

    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path="telegram",
        webhook_url="https://nph-brasil-bot.onrender.com/telegram",
    )


if __name__ == "__main__":
    main()
