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
        [
            InlineKeyboardButton(
                "💎 ENTRAR NO VIP",
                callback_data="entrar_vip"
            )
        ]
    ]

    await update.message.reply_text(
        "🚨Vidios quentes que você quer ?\n\n"
        "Economize MUITO pagando apenas umas vez!!\n\n"
        "Vidios novos todos os dias\n\n"
        "Mais de 3 mil Vidios para não enjoar\n\n"
        "Grupo privado e 100% reservado não mostra quem você é\n\n"
        "Os melhores Vidios estão aqui",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def mostrar_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        f"ID do grupo: {update.effective_chat.id}"
    )


async def entrar_vip(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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

    try:

        result = await asyncio.to_thread(
            sdk.preference().create,
            preference_data
        )

        payment_url = result["response"].get("init_point")

        if not payment_url:
            await query.message.reply_text(
                "❌ Não conseguimos gerar o pagamento."
            )
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    "💳 PAGAR R$ 9,90",
                    url=payment_url
                )
            ]
        ]

        await query.message.reply_text(
            "💳 Pagamento preparado!\n\n"
            "💰 Valor: R$ 9,90\n\n"
            "👇 Clique abaixo para pagar pelo Mercado Pago.\n\n"
            "✅ Após a aprovação, seu acesso será liberado automaticamente.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:

        print(
            "ERRO AO GERAR PAGAMENTO:",
            repr(e),
            flush=True
        )

        await query.message.reply_text(
            "❌ Erro ao gerar pagamento. Tente novamente."
        )


async def telegram_webhook(request):

    try:

        data = await request.json()

        update = Update.de_json(
            data,
            telegram_app.bot
        )

        await telegram_app.update_queue.put(update)

        return web.Response(
            text="OK",
            status=200
        )

    except Exception as e:

        print(
            "ERRO TELEGRAM WEBHOOK:",
            repr(e),
            flush=True
        )

        return web.Response(
            text="OK",
            status=200
        )


async def mercado_pago_webhook(request):

    try:

        print(
            "WEBHOOK MERCADO PAGO RECEBIDO",
            flush=True
        )

        try:
            data = await request.json()
        except Exception:
            data = {}

        print(
            "DADOS WEBHOOK:",
            data,
            flush=True
        )

        payment_id = None

        if isinstance(data, dict):

            data_field = data.get("data")

            if isinstance(data_field, dict):
                payment_id = data_field.get("id")

            if not payment_id:
                payment_id = data.get("id")

        if not payment_id:
            payment_id = request.query.get("data.id")

        if not payment_id:
            payment_id = request.query.get("id")

        if not payment_id:

            print(
                "WEBHOOK SEM PAYMENT_ID",
                flush=True
            )

            return web.Response(
                text="OK",
                status=200
            )

        print(
            "PAYMENT ID:",
            payment_id,
            flush=True
        )

        result = await asyncio.to_thread(
            sdk.payment().get,
            payment_id
        )

        payment = result.get(
            "response",
            {}
        )

        print(
            "PAGAMENTO:",
            payment,
            flush=True
        )

        status = payment.get("status")

        external_reference = payment.get(
            "external_reference"
        )

        amount = payment.get(
            "transaction_amount"
        )

        print(
            "STATUS:",
            status,
            "USUARIO:",
            external_reference,
            "VALOR:",
            amount,
            flush=True
        )

        if (
            status == "approved"
            and external_reference
            and float(amount or 0) >= PRICE
        ):

            user_id = int(
                external_reference
            )

            if not GROUP_ID:

                print(
                    "ERRO: TELEGRAM_GROUP_ID NÃO CONFIGURADO",
                    flush=True
                )

                return web.Response(
                    text="OK",
                    status=200
                )

            expire_date = (
                datetime.now(timezone.utc)
                + timedelta(hours=24)
            )

            invite = await telegram_app.bot.create_chat_invite_link(
                chat_id=GROUP_ID,
                member_limit=1,
                expire_date=expire_date,
                name=f"VIP_{user_id}",
            )

            await telegram_app.bot.send_message(
                chat_id=user_id,
                text=(
                    "✅ PAGAMENTO APROVADO!\n\n"
                    "💎 Seu acesso ao NPH_BRASIL VIP foi liberado.\n\n"
                    "👇 Entre pelo link abaixo:\n"
                    f"{invite.invite_link}\n\n"
                    "⚠️ Este link é individual e permite apenas 1 entrada."
                ),
            )

            print(
                "ACESSO LIBERADO PARA:",
                user_id,
                flush=True
            )

        return web.Response(
            text="OK",
            status=200
        )

    except Exception as e:

        print(
            "ERRO MERCADO PAGO:",
            repr(e),
            flush=True
        )

        return web.Response(
            text="OK",
            status=200
        )


async def home(request):

    return web.Response(
        text="NPH_BRASIL BOT ONLINE"
    )


async def main():

    global telegram_app

    if not TELEGRAM_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN não configurado"
        )

    if not MP_TOKEN:
        raise RuntimeError(
            "MERCADO_PAGO_ACCESS_TOKEN não configurado"
        )

    telegram_app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    telegram_app.add_handler(
        CommandHandler(
            "id",
            mostrar_id
        )
    )

    telegram_app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    telegram_app.add_handler(
        CallbackQueryHandler(
            entrar_vip,
            pattern="^entrar_vip$"
        )
    )

    await telegram_app.initialize()

    await telegram_app.start()

    await telegram_app.bot.set_webhook(
        url=f"{BASE_URL}/telegram"
    )

    app = web.Application()

    app.router.add_get(
        "/",
        home
    )

    app.router.add_post(
        "/telegram",
        telegram_webhook
    )

    app.router.add_post(
        "/mercadopago",
        mercado_pago_webhook
    )

    runner = web.AppRunner(app)

    await runner.setup()

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()

    print(
        "BOT ONLINE",
        flush=True
    )

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
