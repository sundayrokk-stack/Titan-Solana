import os
import threading
from flask import Flask
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

load_dotenv()

# --- 1. STATES ---
(
    START_SCREEN, 
    INTRO_SCREEN, 
    MAIN_MENU,
    WAITING_INPUT,
    WAITING_WITHDRAW_ADDR, 
    WAITING_WITHDRAW_AMT
) = range(6)

# --- 2. WEB SERVER ---
app = Flask(__name__)
@app.route('/')
def health(): return "Titan Online", 200
def run_flask(): app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

# --- 3. UI LAYOUT ---
def main_menu_keyboard():
    # Exactly 14 buttons in a 5-row professional grid
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Sniper", callback_data="btn_sniper"), 
         InlineKeyboardButton("⚖️ DCA", callback_data="btn_dca"), 
         InlineKeyboardButton("🌊 Trenches", callback_data="btn_trenches")],
        [InlineKeyboardButton("💳 Buy", callback_data="btn_buy"), 
         InlineKeyboardButton("💰 Sell", callback_data="btn_sell"), 
         InlineKeyboardButton("📈 Position", callback_data="btn_pos")],
        [InlineKeyboardButton("👥 Copy Trade", callback_data="btn_copy"), 
         InlineKeyboardButton("🎁 Rewards", callback_data="btn_rewards"), 
         InlineKeyboardButton("👀 Watchlist", callback_data="btn_watchlist")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="btn_settings"), 
         InlineKeyboardButton("🤝 Referral", callback_data="btn_ref"), 
         InlineKeyboardButton("💸 Withdraw", callback_data="btn_withdraw")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="btn_refresh"), 
         InlineKeyboardButton("❓ Help", callback_data="btn_help")]
    ])

# --- 4. FLOW HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "━━━━━━━━━━━━━━━\n"
        "⚠️  *IMPORTANT RISK WARNING* ⚠️\n"
        "━━━━━━━━━━━━━━━\n\n"
        "Trading Solana tokens involves high risk\. Prices move fast\! "
        "Never trade money you cannot afford to lose\.\n\n"
        "🙋‍♂️ *SUPPORT:* @ads2defi"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("➡️ CONTINUE", callback_data="go_intro")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    return START_SCREEN

async def show_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = (
        "🚀 *WELCOME TO TITAN TERMINAL*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Titan is the world's fastest Solana trading bot\.\n"
        "• Execute trades in < 1 second\n"
        "• Advanced Sniping & DCA logic\n"
        "• Secure, Encrypted Wallets\n\n"
        "Support: @ads2defi"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 START TRADING", callback_data="go_main")]])
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    return INTRO_SCREEN

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    text = (
        "🏦 *TITAN TRADING TERMINAL*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💳 *Wallet:* `7xKX...v9PQ7L`\n"
        "💰 *Balance:* `0.00 SOL`\n\n"
        "Select a function below to begin\:"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
    return MAIN_MENU

# --- 5. INTERACTIVE BUTTON LOGIC ---
async def handle_all_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Map buttons to their specific prompts
    prompts = {
        "btn_sniper": "🚀 *SNIPER*: Paste the Token CA to begin sniping:",
        "btn_dca": "⚖️ *DCA*: Enter Token CA and buy interval (e.g. `CA 1h`):",
        "btn_buy": "💳 *BUY*: Enter the Token CA you want to buy:",
        "btn_sell": "💰 *SELL*: Enter the Token CA you want to sell:",
        "btn_copy": "👥 *COPY*: Enter the wallet address to follow:",
        "btn_watchlist": "👀 *WATCHLIST*: Enter CA to track:",
    }

    if data in prompts:
        await query.edit_message_text(prompts[data], parse_mode=ParseMode.MARKDOWN_V2)
        context.user_data['current_action'] = data
        return WAITING_INPUT

    if data == "btn_withdraw":
        await query.edit_message_text("💸 *WITHDRAW*: Enter the destination SOL address:")
        return WAITING_WITHDRAW_ADDR

    # Responses for buttons that don't need text input
    instant = {
        "btn_trenches": "🌊 *TRENCHES*: Scanning new tokens on Pump\.fun\.\.\.",
        "btn_pos": "📈 *POSITIONS*: No active trades found\.",
        "btn_rewards": "🎁 *REWARDS*: Balance: `0` points\. Trade to earn\!",
        "btn_settings": "⚙️ *SETTINGS*: Auto-Buy: [OFF] | Slippage: [1%]",
        "btn_ref": "🤝 *REFERRAL*: Your link: `t.me/TitanBot?start=ref_1`",
        "btn_help": "❓ *HELP*: Reach out to @ads2defi for 24/7 support\.",
        "btn_refresh": "🔄 *REFRESHING*\.\.\."
    }

    if data in instant:
        await query.edit_message_text(f"{instant[data]}\n\nClick Refresh to return\.", reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
        return MAIN_MENU

async def process_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This catches the text after user clicks Sniper/Buy/etc
    await update.message.reply_text(f"✅ Received\! Processing your request\.\.\.\nSupport: @ads2defi", parse_mode=ParseMode.MARKDOWN_V2)
    return await show_main_menu(update, context)

# --- 6. MAIN APP SETUP ---
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_SCREEN: [CallbackQueryHandler(show_intro, pattern="^go_intro$")],
            INTRO_SCREEN: [CallbackQueryHandler(show_main_menu, pattern="^go_main$")],
            MAIN_MENU: [
                # This pattern "^btn_" catches all 14 buttons properly
                CallbackQueryHandler(handle_all_buttons, pattern="^btn_"),
                CallbackQueryHandler(show_main_menu, pattern="^btn_refresh$")
            ],
            WAITING_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_text_input)],
            WAITING_WITHDRAW_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_text_input)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    app_bot.add_handler(conv_handler)
    app_bot.run_polling()

if __name__ == '__main__':
    main()
