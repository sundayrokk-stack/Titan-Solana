from flask import Flask, jsonify
import os
import logging
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Telegram Trading Bot",
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

def start_bot():
    """Import and run the bot in a separate thread"""
    try:
        # Import here to avoid circular imports
        from bot import run_bot
        run_bot()
    except Exception as e:
        logging.error(f"Failed to start bot: {e}")

if __name__ == '__main__':
    # Start bot in a background thread
    bot_thread = Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
