from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes, Application, \
    MessageHandler, filters

from app.core.config import tg_conf


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.app = Application.builder().token(self.token).build()
        self.wallet_connected = {}

        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.message.chat_id
        self.wallet_connected[user_id] = False

        inline_keyboard = [[InlineKeyboardButton("🔗 Connect Wallet", callback_data="connect_wallet")]]
        inline_reply_markup = InlineKeyboardMarkup(inline_keyboard)

        await update.message.reply_text(
            "🔥 Hello!\n\n"
            "This bot only sends messages, and you can't chat with it.\n"
            "Click the button below to connect your wallet.",
            reply_markup=inline_reply_markup
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.message.chat_id
        await query.answer()

        if query.data == "connect_wallet":
            self.wallet_connected[user_id] = True

            await query.edit_message_text(
                "✅ Wallet Connected!\n"
                "You can now request an **analytic report** anytime."
            )

            keyboard = [[KeyboardButton("📊 Get Analytic Report")]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

            await query.message.reply_text(
                "Use the button below to request your analytic report.",
                reply_markup=reply_markup
            )

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.message.chat_id
        user_message = update.message.text

        if user_message == "📊 Get Analytic Report":
            if self.wallet_connected.get(user_id, False):
                await self.send_analytic_report(update)
            else:
                inline_keyboard = [[InlineKeyboardButton("🔗 Connect Wallet", callback_data="connect_wallet")]]
                inline_reply_markup = InlineKeyboardMarkup(inline_keyboard)

                await update.message.reply_text(
                    "⚠️ Please **connect your wallet first** using the button below.",
                    reply_markup=inline_reply_markup
                )
        else:
            await update.message.reply_text("⚠️ This bot does not accept messages. Please use the available buttons.")

    async def send_analytic_report(self, update: Update):
        analytic_report = (
            "📊 **Analytic Report**\n"
            "📈 Market analytics: [Insert detailed analysis here]."
        )
        await update.message.reply_text(analytic_report)

    def run(self):
        print("Bot is running...")
        self.app.run_polling()


if __name__ == "__main__":
    bot = TelegramBot(tg_conf.TG_TOKEN)
    bot.run()
