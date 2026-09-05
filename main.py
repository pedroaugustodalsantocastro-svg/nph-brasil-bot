import os
import asyncio
from datetime import datetime, timedelta, timezone

import mercadopago
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
MP_TOKEN = os.environ.get("MERCADO_PAGO_ACCESS_TOKEN")
GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID")

BASE_URL = "https://nph-brasil-bot.onrender.com"
PRICE = 9.90

sdk = mercadopago.SDK(MP_TOKEN)


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
async def mostrar_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"ID do grupo: {update.effective_chat.id}")

async def entrar_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    preference_data = {
        "items": [
            {
                "title": "Acesso NPH_BRASIL VIP",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": PRICE,
            }
        ],
        "external_reference": str(user_id),
        "notification_url": f"{BASE_URL}/mercadopago",
    }

    result = await asyncio.to_thread(
        sdk.preference().create,
        preference_data
    )

    payment_url = result["response"].get("init_point")

    if not payment_url:
        await query.message.reply_text(
            "❌ Não conseguimos gerar o pagamento. Tente novamente."
        )
        return

    keyboard = [
        [InlineKeyboardButton("💳 PAGAR R$ 9,90", url=payment_url)]
    ]

    await query.message.reply_text(
        "💳 Pagamento preparado!\n\n"
        "💰 Valor: R$ 9,90\n\n"
        "👇 Clique abaixo para pagar pelo Mercado Pago.\n\n"
        "✅ Após a aprovação, seu acesso será liberado automaticamente.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def telegram_webhook(request):
    data = await request.json()

    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.update_queue.put(update)

    return web.Response(text="OK")


async def mercado_pago_webhook(request):
    try:
        data = await request.json()

        payment_id = None

        if isinstance(data, dict):
            payment_id = data.get("data", {}).get("id")

        if not payment_id:
            payment_id = request.query.get("data.id")

        if not payment_id:
            return web.Response(text="OK")

        result = await asyncio.to_thread(
            sdk.payment().get,
            payment_id
        )

        payment = result.get("response", {})

        status = payment.get("status")
        external_reference = payment.get("external_reference")
        amount = payment.get("transaction_amount")

        if (
            status == "approved"
            and external_reference
            and float(amount or 0) >= PRICE
        ):
            user_id = int(external_reference)

            expire_date = datetime.now(timezone.utc) + timedelta(hours=24)

            invite = await telegram_app.bot.create_chat_invite_link(
                chat_id=GROUP_ID,
                member_limit=1,
                expire_date=expire_date,
                name=f"VIP-{user_id}",
            )

            await telegram_app.bot.send_message(
                chat_id=user_id,
                text=(
                    "✅ PAGAMENTO APROVADO!\n\n"
                    "💎 Seu acesso ao NPH_BRASIL VIP foi liberado.\n\n"
                    "👇 Entre pelo link abaixo:\n"
                    f"{invite.invite_link}\n\n"
                    "⚠️ Este link é individual e expira em 24 horas."
                ),
            )

        return web.Response(text="OK")

    except Exception as e:
        print("Erro Mercado Pago:", e)
        return web.Response(text="OK")


async def home(request):
    return web.Response(text="NPH_BRASIL BOT ONLINE")


async def main():
    global telegram_app

    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado")

    if not MP_TOKEN:
        raise RuntimeError("MERCADO_PAGO_ACCESS_TOKEN não configurado")

    telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
telegram_app.add_handler(CommandHandler("id", mostrar_id))
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(
        CallbackQueryHandler(entrar_vip, pattern="^entrar_vip$")
    )

    await telegram_app.initialize()
    await telegram_app.start()

    await telegram_app.bot.set_webhook(
        url=f"{BASE_URL}/telegram"
    )

    app = web.Application()

    app.router.add_get("/", home)
    app.router.add_post("/telegram", telegram_webhook)
    app.router.add_post("/mercadopago", mercado_pago_webhook)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()

    print("BOT ONLINE")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
