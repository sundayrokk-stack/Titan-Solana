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
    START_SCREEN, INTRO_SCREEN, MAIN_MENU,
    # Multi-step process states
    WAITING_CA, WAITING_AMOUNT, WAITING_DCA_TIME,
    WAITING_WITHDRAW_ADDR, WAITING_WITHDRAW_AMT,
    WAITING_COPY_WALLET
) = range(9)

# --- 2. WEB SERVER ---
app = Flask(__name__)
@app.route('/')
def health(): return "Titan Active", 200
def run_flask(): app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

# --- 3. UI LAYOUT ---
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

# --- 4. NAVIGATION FLOW ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "━━━━━━━━━━━━━━━━━━\n"
        "⚠️  *IMPORTANT RISK WARNING* ⚠️\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Trading digital assets involves significant risk\. "
        "Solana prices are highly volatile\. Only invest what you can afford to lose\.\n\n"
        "🙋‍♂️ *SUPPORT:* Contact @BlockSavvyMx"
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
        "Titan is the fastest trading engine on Solana\.\n"
        "• Direct Jupiter V6 Smart Routing\n"
        "• Instant Buy/Sell Execution\n"
        "• Advanced Sniping & DCA tools\n\n"
        "🙋‍♂️ *SUPPORT:* @BlockSavvyMx"
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
        "Select a function below to begin trading\:"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
    return MAIN_MENU

# --- 5. INTERACTIVE MULTI-STEP LOGIC ---

# Flow: Click Button -> Ask CA -> User Sends CA -> Ask Amount -> User Sends Amount -> Final Response
async def handle_trading_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.replace("btn_", "")
    context.user_data['active_action'] = action

    if action in ["sniper", "buy", "sell", "dca"]:
        await query.edit_message_text(f"🎯 *{action.upper()} MODE*\n\nPlease enter the *Contract Address (CA)* of the token:", parse_mode=ParseMode.MARKDOWN_V2)
        return WAITING_CA
    
    elif action == "copy":
        await query.edit_message_text("👥 *COPY TRADING*\nPaste the Solana wallet address you wish to follow:", parse_mode=ParseMode.MARKDOWN_V2)
        return WAITING_COPY_WALLET

    elif action == "withdraw":
        await query.edit_message_text("💸 *WITHDRAWAL*\nEnter the destination Solana wallet address:", parse_mode=ParseMode.MARKDOWN_V2)
        return WAITING_WITHDRAW_ADDR

    # Instant feedback buttons
    instant = {
        "trenches": "🌊 *TRENCHES*: Scanning new tokens on Pump\.fun\.\.\.",
        "pos": "📈 *POSITIONS*: No active trades found\.",
        "rewards": "🎁 *REWARDS*: Balance: `0` points\. Trade to earn\!",
        "settings": "⚙️ *SETTINGS*: Auto-Buy: [OFF] | Priority: [Turbo]",
        "ref": "🤝 *REFERRAL*: Your link: `t.me/TitanBot?start=ref`",
        "help": "❓ *HELP*: Contact @BlockSavvyMx for 24/7 support\.",
    }
    await query.edit_message_text(f"{instant.get(action)}\n\nClick Refresh to return to menu\.", reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
    return MAIN_MENU

# --- STEP 2: Handle CA and ask for Amount ---
async def process_ca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ca'] = update.message.text
    action = context.user_data.get('active_action')
    await update.message.reply_text(f"✅ CA Detected: `{context.user_data['ca']}`\n\nNow, enter the amount of *SOL* to use for this {action}:", parse_mode=ParseMode.MARKDOWN_V2)
    return WAITING_AMOUNT

# --- STEP 3: Final confirmation and return to menu ---
async def process_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = update.message.text
    action = context.user_data.get('active_action')
    ca = context.user_data.get('ca')
    
    await update.message.reply_text(
        f"🚀 *{action.upper()} INITIATED*\n\n"
        f"Token: `{ca}`\n"
        f"Amount: `{amount} SOL`\n\n"
        f"Processing through Jupiter V6 API\.\.\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return await show_main_menu(update, context)

# --- 6. MAIN APP ---
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_SCREEN: [CallbackQueryHandler(show_intro, pattern="^go_intro$")],
            INTRO_SCREEN: [CallbackQueryHandler(show_main_menu, pattern="^go_main$")],
            MAIN_MENU: [
                CallbackQueryHandler(handle_trading_buttons, pattern="^btn_"),
                CallbackQueryHandler(show_main_menu, pattern="^btn_refresh$"),
            ],
            WAITING_CA: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_ca)],
            WAITING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_final)],
            WAITING_WITHDRAW_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_ca)], # Reuse logic
            WAITING_COPY_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_ca)],   # Reuse logic
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    app_bot.add_handler(conv_handler)
    app_bot.run_polling()

if __name__ == '__main__':
    main()
