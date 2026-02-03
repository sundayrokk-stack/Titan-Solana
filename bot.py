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
    WAITING_INPUT, # Generic state for button-specific questions
    WAITING_WITHDRAW_ADDR, WAITING_WITHDRAW_AMT
) = range(6)

# --- 2. WEB SERVER (For Render) ---
app = Flask(__name__)
@app.route('/')
def health(): return "Titan Online", 200
def run_flask(): app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

# --- 3. MAIN MENU UI (5-Row Grid) ---
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

# --- 4. NAVIGATION HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "━━━━━━━━━━━━━━━\n"
        "⚠️  *IMPORTANT RISK WARNING* ⚠️\n"
        "━━━━━━━━━━━━━━━\n\n"
        "Trading digital assets involves significant risk\. "
        "Solana prices are highly volatile\. Only invest what you can afford to lose\.\n\n"
        "🙋‍♂️ *SUPPORT:* Contact @ads2defi only\."
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
        "Click below to initialize your secure wallet\."
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

# --- 5. INTERACTIVE BUTTON LOGIC (ALL 14 BUTTONS) ---
async def handle_trading_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    btn_type = query.data.replace("btn_", "")

    # Define prompts for buttons that need user text input
    input_prompts = {
        "sniper": "🚀 *SNIPER MODE*\nPlease enter the Token Contract Address (CA) you wish to snipe:",
        "dca": "⚖️ *DCA STRATEGY*\nEnter the Token CA and interval (e.g., `CA 1h`):",
        "buy": "💳 *QUICK BUY*\nEnter the Token Contract Address (CA) to purchase:",
        "sell": "💰 *QUICK SELL*\nEnter the Token Contract Address (CA) to sell:",
        "copy": "👥 *COPY TRADING*\nEnter the Solana wallet address you want to follow:",
        "watchlist": "👀 *WATCHLIST*\nEnter the Token CA to add to your alerts:",
    }

    if btn_type in input_prompts:
        await query.edit_message_text(input_prompts[btn_type], parse_mode=ParseMode.MARKDOWN_V2)
        context.user_data['last_action'] = btn_type
        return WAITING_INPUT
    
    if btn_type == "withdraw":
        await query.edit_message_text("💸 *WITHDRAWAL*\nPlease enter the destination Solana wallet address:")
        return WAITING_WITHDRAW_ADDR

    # Instant response buttons
    instant_responses = {
        "trenches": "🌊 *TRENCHES*: Scanning new migrations on Pump\.fun\.\.\.",
        "pos": "📈 *POSITIONS*: No active trading positions found\.",
        "rewards": "🎁 *REWARDS*: You currently have `0` points\. Trade to earn\!",
        "settings": "⚙️ *SETTINGS*\n• Auto-buy: OFF\n• Slipper: 0\.5%\n• Priority: Turbo",
        "ref": "🤝 *REFERRAL PROGRAM*\nYour link: `t.me/TitanBot?start=ref_user`",
        "help": "❓ *HELP & SUPPORT*\nContact @ads2defi for technical assistance\."
    }
    
    msg = instant_responses.get(btn_type, "Action initialized\.")
    await query.edit_message_text(f"{msg}\n\nClick Refresh to return to main menu\.", reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
    return MAIN_MENU

# --- 6. INPUT PROCESSORS ---
async def process_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    action = context.user_data.get('last_action', 'trade')
    await update.message.reply_text(f"✅ *{action.upper()} RECEIVED*\nProcessing `{user_text}`\.\.\.", parse_mode=ParseMode.MARKDOWN_V2)
    return await show_main_menu(update, context)

async def process_withdraw_addr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['w_addr'] = update.message.text
    await update.message.reply_text("Wallet accepted\. Now enter the amount of SOL to withdraw:")
    return WAITING_WITHDRAW_AMT

async def process_withdraw_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amt = update.message.text
    addr = context.user_data.get('w_addr')
    await update.message.reply_text(f"📤 *WITHDRAWAL INITIATED*\nAmount: {amt} SOL\nTo: `{addr}`", parse_mode=ParseMode.MARKDOWN_V2)
    return await show_main_menu(update, context)

# --- 7. MAIN APP ---
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
                CallbackQueryHandler(start, pattern="^go_intro$"), # Allows reset
            ],
            WAITING_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_user_input)],
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
