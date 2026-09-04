import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

app = Flask(__name__)


@app.route("/")
def home():
    return "NPH_BRASIL BOT ONLINE", 200


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
        "⏳ Aguarde enquanto preparamos o pagamento."
    )


def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado")

    Thread(target=run_web, daemon=True).start()

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(entrar_vip, pattern="^entrar_vip$"))

    application.run_polling()


if __name__ == "__main__":
    main()
