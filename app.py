from flask import Flask, jsonify
import threading
import os
import asyncio
import subprocess
import sys

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

def run_bot():
    """Run the Telegram bot in a subprocess"""
    try:
        # Run the bot
        subprocess.run([sys.executable, "bot.py"])
    except Exception as e:
        print(f"Bot error: {e}")

if __name__ == '__main__':
    # Get port from environment (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
