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

# --- STATES ---
(
    # Navigation States
    START_SCREEN, 
    INTRO_SCREEN, 
    MAIN_MENU,
    # Trading Input States
    WAITING_SNIPER_CA,
    WAITING_DCA_TOKEN,
    WAITING_WITHDRAW_ADDR,
    WAITING_WITHDRAW_AMT
) = range(7)

# --- FLASK SERVER ---
app = Flask(__name__)
@app.route('/')
def health(): return "Titan Online", 200
def run_flask(): app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

# --- UI KEYBOARDS ---
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

# --- LOGIC HANDLERS ---

# 1. Start Command -> Risk Warning
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚠️ *RISK WARNING*\n\n"
        "Trading digital assets involves significant risk\. Prices can be highly volatile\. "
        "Only invest what you can afford to lose\.\n\n"
        "🙋‍♂️ *Support:* Only contact @ads2defi"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("➡️ Continue", callback_data="go_intro")]])
    
    if update.message:
        msg = await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
        try: await context.bot.pin_chat_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
        except: pass
    else: # If coming from a callback
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    
    return START_SCREEN

# 2. Continue -> Introduction
async def show_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "🚀 *Introduction to Solana Trading*\n\n"
        "Titan is the fastest trading terminal on Solana\.\n"
        "• High speed execution\n"
        "• Direct Jupiter V6 Routing\n"
        "• Advanced sniping & DCA tools"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Start Trading", callback_data="go_main")]])
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    return INTRO_SCREEN

# 3. Start Trading -> Main Menu (14 Buttons)
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    
    wallet = "`7xKX...v9PQ7L`"
    text = (
        "🏦 *Titan Trading Terminal*\n\n"
        f"💳 *Wallet:* {wallet}\n"
        "Balance: *0\.00 SOL*\n\n"
        "Select a tool below to begin\:"
    )
    
    if query:
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN_V2)
    return MAIN_MENU

# --- TOOL HANDLERS (Example: Sniper & Withdraw) ---

async def tool_sniper_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🚀 *Sniper Mode*\nEnter the Token Contract Address (CA) you want to snipe:", parse_mode=ParseMode.MARKDOWN_V2)
    return WAITING_SNIPER_CA

async def tool_sniper_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ca = update.message.text
    await update.message.reply_text(f"✅ CA Detected: `{ca}`\nSearching for liquidity pools\.\.\. Please wait\.", parse_mode=ParseMode.MARKDOWN_V2)
    # Return to main menu after processing
    return await show_main_menu(update, context)

async def tool_withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("💸 *Withdraw*\nEnter the destination Solana wallet address:", parse_mode=ParseMode.MARKDOWN_V2)
    return WAITING_WITHDRAW_ADDR

async def tool_withdraw_addr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tmp_addr'] = update.message.text
    await update.message.reply_text("Enter the amount of SOL to withdraw:")
    return WAITING_WITHDRAW_AMT

async def tool_withdraw_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amt = update.message.text
    addr = context.user_data['tmp_addr']
    await update.message.reply_text(f"📤 Withdrawal of {amt} SOL to `{addr}` initiated\!", parse_mode=ParseMode.MARKDOWN_V2)
    return await show_main_menu(update, context)

# Generic "Coming Soon" for other buttons to keep them functional
async def placeholder_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(f"Feature '{query.data}' coming in next update!", show_alert=True)
    return MAIN_MENU

# --- MAIN ---
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    app_bot = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_SCREEN: [CallbackQueryHandler(show_intro, pattern="^go_intro$")],
            INTRO_SCREEN: [CallbackQueryHandler(show_main_menu, pattern="^go_main$")],
            MAIN_MENU: [
                CallbackQueryHandler(tool_sniper_start, pattern="^btn_sniper$"),
                CallbackQueryHandler(tool_withdraw_start, pattern="^btn_withdraw$"),
                CallbackQueryHandler(show_main_menu, pattern="^btn_refresh$"),
                CallbackQueryHandler(placeholder_btn, pattern="^btn_") # Catches all buttons starting with btn_
            ],
            WAITING_SNIPER_CA: [MessageHandler(filters.TEXT & ~filters.COMMAND, tool_sniper_process)],
            WAITING_WITHDRAW_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, tool_withdraw_addr)],
            WAITING_WITHDRAW_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tool_withdraw_final)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    app_bot.add_handler(conv_handler)
    app_bot.run_polling()

if __name__ == '__main__':
    main()
