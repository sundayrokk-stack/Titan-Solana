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

# --- 1. DEFINING ALL STATES ---
(
    START_SCREEN, INTRO_SCREEN, MAIN_MENU,
    WAITING_INPUT, # Generic state for simple text responses
    WAITING_WITHDRAW_ADDR, WAITING_WITHDRAW_AMT
) = range(6)

# --- 2. WEB SERVER FOR RENDER ---
app = Flask(__name__)
@app.route('/')
def health(): return "Bot Online", 200
def run_flask(): app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

# --- 3. THE ORIGINAL 5-ROW GRID ---
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

# --- 4. NAVIGATION HANDLERS (THE ORDER) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "⚠️ *RISK WARNING*\n\nTrading is risky\. Contact @ads2defi for support\."
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("➡️ Continue", callback_data="go_intro")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    return START_SCREEN

async def show_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = "🚀 *Welcome to Titan*\nThe fastest Solana trading terminal\."
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

# --- 5. INTERACTIVE BUTTON LOGIC ---
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.replace("btn_", "")
    
    # Logic for buttons requiring input
    if action in ["sniper", "dca", "buy", "sell", "copy", "watchlist"]:
        prompts = {
            "sniper": "🚀 *SNIPER*: Enter the Token CA to snipe:",
            "dca": "⚖️ *DCA*: Enter Token CA and Interval (e.g., CA 1h):",
            "buy": "💳 *BUY*: Enter the Token CA you want to buy:",
            "sell": "💰 *SELL*: Enter the Token CA you want to sell:",
            "copy": "👥 *COPY*: Enter the wallet address to follow:",
            "watchlist": "👀 *WATCHLIST*: Enter CA to add to alerts:"
        }
        await query.edit_message_text(prompts[action], parse_mode=ParseMode.MARKDOWN_V2)
        return WAITING_INPUT

    # Logic for instant response buttons
    elif action == "withdraw":
        await query.edit_message_text("💸 *WITHDRAW*: Enter destination address:")
        return WAITING_WITHDRAW_ADDR
    
    responses = {
        "trenches": "🌊 *Trenches*: Scanning for new migrations\.\.\.",
        "pos": "📈 *Positions*: You have no active trades\.",
        "rewards": "🎁 *Rewards*: 0\.00 Points earned\. Trade to earn\!",
        "settings": "⚙️ *Settings*: Auto-buy: OFF | Priority: Medium",
        "ref": "🤝 *Referral*: Your link: `t.me/TitanBot?start=ref123`",
        "help": "❓ *Help*: Use /start to reset\. Support: @ads2defi"
    }
    await query.edit_message_text(f"{responses[action]}\n\nClick Refresh to return\.", reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
    return MAIN_MENU

# --- 6. INPUT PROCESSORS ---
async def process_generic_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"✅ Data processed: `{update.message.text}`\nReturning to menu\.\.\.", parse_mode=ParseMode.MARKDOWN_V2)
    return await show_main_menu(update, context)

async def process_withdraw_addr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['withdraw_addr'] = update.message.text
    await update.message.reply_text("Address saved\. Now enter amount to withdraw:")
    return WAITING_WITHDRAW_AMT

async def process_withdraw_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📤 Withdrawal of {update.message.text} SOL to `{context.user_data['withdraw_addr']}` initiated\!", parse_mode=ParseMode.MARKDOWN_V2)
    return await show_main_menu(update, context)

# --- 7. MAIN APPLICATION ---
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_SCREEN: [CallbackQueryHandler(show_intro, pattern="^go_intro$")],
            INTRO_SCREEN: [CallbackQueryHandler(show_main_menu, pattern="^go_main$")],
            MAIN_MENU: [
                CallbackQueryHandler(handle_button_click, pattern="^btn_"),
                CallbackQueryHandler(show_main_menu, pattern="^btn_refresh$")
            ],
            WAITING_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_generic_input)],
            WAITING_WITHDRAW_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_addr)],
            WAITING_WITHDRAW_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_final)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    app_bot.add_handler(conv_handler)
    app_bot.run_polling()

if __name__ == '__main__':
    main()
