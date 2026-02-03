import os
import logging
import asyncio
import threading
import httpx
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

# --- CONFIG & STATES ---
# Conversation States
SNIPER_ADDR, DCA_SETUP, WITHDRAW_ADDR, WITHDRAW_AMT = range(4)
JUPITER_API = "https://quote-api.jup.ag/v6"

# --- FLASK SERVER (For Render Keep-Alive) ---
app = Flask(__name__)
@app.route('/')
def health(): return "Titan Active", 200
def run_flask(): app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

# --- UI COMPONENTS ---
def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🚀 Sniper", callback_data="menu_sniper"), 
         InlineKeyboardButton("⚖️ DCA", callback_data="menu_dca"), 
         InlineKeyboardButton("🌊 Trenches", callback_data="menu_trenches")],
        [InlineKeyboardButton("💳 Buy", callback_data="menu_buy"), 
         InlineKeyboardButton("💰 Sell", callback_data="menu_sell"), 
         InlineKeyboardButton("📈 Position", callback_data="menu_pos")],
        [InlineKeyboardButton("👥 Copy Trade", callback_data="menu_copy"), 
         InlineKeyboardButton("🎁 Rewards", callback_data="menu_rewards"), 
         InlineKeyboardButton("👀 Watchlist", callback_data="menu_watchlist")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings"), 
         InlineKeyboardButton("🤝 Referral", callback_data="menu_ref"), 
         InlineKeyboardButton("💸 Withdraw", callback_data="menu_withdraw")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="menu_refresh"), 
         InlineKeyboardButton("❓ Help", callback_data="menu_help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *Titan on Solana* — Professional Trading Suite\n\n"
        "💳 *Wallet:* `7xKX...v9PQ7L`\n"
        "💰 *Balance:* `0.00 SOL`\n\n"
        "For Support, only contact @ads2defi"
    )
    msg = await update.message.reply_text(text, reply_markup=get_main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
    try: await context.bot.pin_chat_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
    except: pass
    return ConversationHandler.END

# --- 🚀 SNIPER LOGIC ---
async def sniper_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🚀 *Sniper Mode*\nPaste the Token Contract Address (CA) to snipe:", parse_mode=ParseMode.MARKDOWN_V2)
    return SNIPER_ADDR

async def sniper_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ca = update.message.text
    # Validation logic here
    await update.message.reply_text(f"✅ Target Locked: `{ca}`\nSetting up Auto-Buy parameters...", parse_mode=ParseMode.MARKDOWN_V2)
    return ConversationHandler.END

# --- 💸 WITHDRAW LOGIC ---
async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("💸 *Withdraw*\nEnter destination Solana address:", parse_mode=ParseMode.MARKDOWN_V2)
    return WITHDRAW_ADDR

async def withdraw_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['withdraw_addr'] = update.message.text
    await update.message.reply_text("Enter amount of SOL to withdraw:")
    return WITHDRAW_AMT

async def withdraw_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = update.message.text
    addr = context.user_data['withdraw_addr']
    await update.message.reply_text(f"🚀 Sending {amount} SOL to `{addr}`...")
    return ConversationHandler.END

# --- 🌊 TRENCHES (API DATA) ---
async def trenches_feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    # Mock data - in production, fetch from DexScreener/Helius API
    text = "🌊 *Live from the Trenches*\n\n1. $PUMP - Liq: $50k\n2. $DUMP - Liq: $12k\n\n*High Risk Detected!*"
    await update.callback_query.edit_message_text(text, reply_markup=get_main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)

# --- 📈 POSITION (PNL) ---
async def position_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = (
        "📈 *Open Positions*\n\n"
        "💎 *SOL:* 0.00 (+$0.00)\n"
        "Total PnL: *+0.00%*"
    )
    keyboard = [[
        InlineKeyboardButton("Sell 25%", callback_data="s25"),
        InlineKeyboardButton("Sell 50%", callback_data="s50"),
        InlineKeyboardButton("Sell 100%", callback_data="s100")
    ], [InlineKeyboardButton("⬅️ Back", callback_data="menu_refresh")]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN_V2)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Action cancelled.")
    return ConversationHandler.END

# --- MAIN RUNNER ---
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # Conversation Handler for Sniper & Withdraw
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(sniper_start, pattern="^menu_sniper$"),
            CallbackQueryHandler(withdraw_start, pattern="^menu_withdraw$"),
        ],
        states={
            SNIPER_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, sniper_process)],
            WITHDRAW_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_address)],
            WITHDRAW_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_final)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(conv_handler)
    app_bot.add_handler(CallbackQueryHandler(trenches_feed, pattern="^menu_trenches$"))
    app_bot.add_handler(CallbackQueryHandler(position_check, pattern="^menu_pos$"))
    app_bot.add_handler(CallbackQueryHandler(start, pattern="^menu_refresh$"))

    app_bot.run_polling()

if __name__ == "__main__":
    main()
