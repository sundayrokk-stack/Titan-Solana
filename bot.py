import os
import logging
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

# --- EXTENDED STATES ---
(
    START_SCREEN, INTRO_SCREEN, MAIN_MENU,
    WAITING_SNIPER_CA, WAITING_DCA_TOKEN, WAITING_WITHDRAW_ADDR, 
    WAITING_WITHDRAW_AMT, WAITING_BUY_CA, WAITING_SELL_CA,
    WAITING_COPY_TARGET, WAITING_WATCHLIST_ADD
) = range(11)

# --- FLASK SERVER (For Render) ---
app = Flask(__name__)
@app.route('/')
def health(): return "Titan Operational", 200
def run_flask(): app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

# --- THE 5-ROW GRID KEYBOARD ---
def main_menu_keyboard():
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

# --- NAVIGATION FLOW ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "⚠️ *RISK WARNING*\n\nSolana trading is volatile\. Invest only what you can lose\.\n\n🙋‍♂️ *Support:* @ads2defi"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("➡️ Continue", callback_data="go_intro")]])
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    return START_SCREEN

async def show_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = "🚀 *Titan Solana Terminal*\nFastest swaps via Jupiter V6\."
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Start Trading", callback_data="go_main")]])
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    return INTRO_SCREEN

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query: await update.callback_query.answer()
    text = "🏦 *Titan Main Terminal*\n\n💳 *Wallet:* `7xKX...v9PQ7L`\n💰 *Balance:* `0.00 SOL`"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
    return MAIN_MENU

# --- INTERACTIVE BUTTON LOGIC ---

async def handle_sniper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("🚀 *SNIPER*\nEnter the Contract Address (CA) to monitor for launch:", parse_mode=ParseMode.MARKDOWN_V2)
    return WAITING_SNIPER_CA

async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("💳 *BUY*\nEnter the Token CA you want to purchase:", parse_mode=ParseMode.MARKDOWN_V2)
    return WAITING_BUY_CA

async def handle_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("💸 *WITHDRAW*\nEnter destination wallet address:", parse_mode=ParseMode.MARKDOWN_V2)
    return WAITING_WITHDRAW_ADDR

async def handle_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Scanning wallet for PnL...", show_alert=False)
    # logic to fetch tokens
    await update.callback_query.edit_message_text("📈 *POSITIONS*\nNo active positions found\.", reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
    return MAIN_MENU

# --- MESSAGE PROCESSORS ---

async def process_ca_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ca = update.message.text
    await update.message.reply_text(f"✅ Received: `{ca}`\nExecuting trade logic via Jupiter V6\.\.\.", parse_mode=ParseMode.MARKDOWN_V2)
    return await show_main_menu(update, context)

# --- MAIN APP ---
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_SCREEN: [CallbackQueryHandler(show_intro, pattern="^go_intro$")],
            INTRO_SCREEN: [CallbackQueryHandler(show_main_menu, pattern="^go_main$")],
            MAIN_MENU: [
                CallbackQueryHandler(handle_sniper, pattern="^btn_sniper$"),
                CallbackQueryHandler(handle_buy, pattern="^btn_buy$"),
                CallbackQueryHandler(handle_withdraw, pattern="^btn_withdraw$"),
                CallbackQueryHandler(handle_position, pattern="^btn_pos$"),
                CallbackQueryHandler(show_main_menu, pattern="^btn_refresh$"),
                # Add individual handlers for Rewards, Help, etc., similarly
            ],
            WAITING_SNIPER_CA: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_ca_input)],
            WAITING_BUY_CA: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_ca_input)],
            WAITING_WITHDRAW_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_ca_input)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    app_bot.add_handler(conv_handler)
    app_bot.run_polling()

if __name__ == '__main__':
    main()
