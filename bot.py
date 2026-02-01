import os
import logging
from dotenv import load_dotenv
import asyncio
import random
import string
from typing import Dict, Any

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

# Generate a dummy Solana wallet address for the user
def generate_dummy_wallet() -> str:
    """Generate a dummy Solana wallet address"""
    chars = string.ascii_letters + string.digits
    return f"Solana: `{''.join(random.choices(chars, k=44))}`"

# User session data
user_sessions: Dict[int, Dict[str, Any]] = {}

# ========== STAGE 1: RISK WARNING ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with risk warning"""
    
    # Generate wallet for user if not exists
    user_id = update.effective_user.id
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'wallet': generate_dummy_wallet(),
            'stage': 'start'
        }
    
    risk_warning = (
        "⚠️ *RISK WARNING*\n\n"
        "▪️ *Trading involves substantial risk*\n"
        "▪️ *Past performance ≠ future results*\n"
        "▪️ *You may lose your entire investment*\n"
        "▪️ *Only trade with risk capital*\n"
        "▪️ *This is not financial advice*\n\n"
        "────────────────\n"
        "*INTRODUCTION*\n\n"
        "Welcome to *Solana Trading Pro* - The ultimate automated "
        "trading solution for Solana ecosystem.\n\n"
        "• *Fast Swaps*: Instant MEV-protected trades\n"
        "• *Limit Orders*: Advanced order types\n"
        "• *Copy Trading*: Mirror top traders\n"
        "• *DCA Strategy*: Dollar-cost averaging\n"
        "• *Portfolio Tracking*: Real-time P&L\n\n"
        "*By continuing, you accept all risks and terms.*"
    )
    
    keyboard = [[
        InlineKeyboardButton(
            "➡️ Continue", 
            callback_data="continue_to_intro"
        )
    ]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            risk_warning,
            reply_markup=reply_markup,
            parse_mode='MarkdownV2'
        )
    else:
        await update.callback_query.edit_message_text(
            risk_warning,
            reply_markup=reply_markup,
            parse_mode='MarkdownV2'
        )

# ========== STAGE 2: INTRODUCTION ==========
async def intro_to_trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show trading introduction"""
    
    intro_message = (
        "🚀 *SOLANA TRADING PRO*\n\n"
        "*Professional Trading Tools at Your Fingertips*\n\n"
        "🔹 *Fast Swaps*\n"
        "Instant token swaps with MEV protection and best price routing\\.\n\n"
        "🔹 *Limit Orders*\n"
        "Set buy/sell targets with advanced order types\\.\n\n"
        "🔹 *Copy Trading*\n"
        "Automatically mirror trades from top performers\\.\n\n"
        "🔹 *DCA Strategy*\n"
        "Dollar\\-cost averaging with automated execution\\.\n\n"
        "🔹 *Real\\-time Positions*\n"
        "Track your P&L with detailed analytics\\.\n\n"
        "────────────────\n"
        "*Ready to start trading?*"
    )
    
    keyboard = [[
        InlineKeyboardButton(
            "🚀 Start Trading", 
            callback_data="start_trading"
        )
    ]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        intro_message,
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )

# ========== STAGE 3: MAIN TRADING MENU ==========
async def main_trading_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display main trading menu with grid layout"""
    
    user_id = update.effective_user.id
    wallet_address = user_sessions.get(user_id, {}).get('wallet', generate_dummy_wallet())
    
    menu_message = (
        "🏦 *MAIN TRADING MENU*\n\n"
        f"*{wallet_address}*\n\n"
        "────────────────\n"
        "*Balance:* `$1,250.75`\n"
        "*PnL (24h):* `+$45.30` 📈\n"
        "*Active Positions:* `3`\n\n"
        "*Select an option:*"
    )
    
    # Create grid layout buttons (5 rows, 2 columns)
    keyboard = [
        # Row 1
        [
            InlineKeyboardButton("💰 Buy", callback_data="action_buy"),
            InlineKeyboardButton("📉 Sell", callback_data="action_sell")
        ],
        # Row 2
        [
            InlineKeyboardButton("⏰ Limit Orders", callback_data="action_limits"),
            InlineKeyboardButton("📊 DCA", callback_data="action_dca")
        ],
        # Row 3
        [
            InlineKeyboardButton("📈 Positions", callback_data="action_positions"),
            InlineKeyboardButton("👥 Copy Trade", callback_data="action_copy")
        ],
        # Row 4
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="action_settings"),
            InlineKeyboardButton("👥 Referrals", callback_data="action_referrals")
        ],
        # Row 5
        [
            InlineKeyboardButton("💸 Withdraw", callback_data="action_withdraw"),
            InlineKeyboardButton("🔄 Refresh", callback_data="action_refresh")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        menu_message,
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )

# ========== ACTION HANDLERS ==========
async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle various trading actions"""
    
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == "action_refresh":
        # Refresh the main menu
        await main_trading_menu(update, context)
    else:
        # For other actions, show a placeholder
        action_names = {
            "action_buy": "💰 Buy",
            "action_sell": "📉 Sell",
            "action_limits": "⏰ Limit Orders",
            "action_dca": "📊 DCA",
            "action_positions": "📈 Positions",
            "action_copy": "👥 Copy Trading",
            "action_settings": "⚙️ Settings",
            "action_referrals": "👥 Referrals",
            "action_withdraw": "💸 Withdraw"
        }
        
        action_name = action_names.get(action, "Action")
        
        message = (
            f"{action_name}\n\n"
            "────────────────\n\n"
            "*This feature is currently under development*\\.\n\n"
            "Check back soon for updates\\!"
        )
        
        keyboard = [[
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="start_trading")
        ]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='MarkdownV2'
        )

# ========== CALLBACK QUERY HANDLER ==========
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == "continue_to_intro":
        await intro_to_trading(update, context)
    elif callback_data == "start_trading":
        await main_trading_menu(update, context)
    elif callback_data.startswith("action_"):
        await handle_action(update, context)
    else:
        await start(update, context)

# ========== MAIN FUNCTION ==========
async def main():
    """Start the bot"""
    
    # Create Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start bot
    logger.info("Starting bot...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    asyncio.run(main())
