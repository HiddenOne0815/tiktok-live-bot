import os, re, time, shlex, subprocess
from datetime import datetime
import requests
from telegram import Bot

from flask import Flask
import threading

app = Flask(__name__)

@app.route("/")
@app.route("/ping")
def health():
    return "ok", 200

def run_flask():
    app.run(host="0.0.0.0", port=10000)


# ====== EINSTELLUNGEN ======
TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID         = os.getenv("CHAT_ID", "")
TIKTOK_USERS    = [u.strip().lstrip("@") for u in os.getenv("TIKTOK_USERS","").split(",") if u.strip()]
CHECK_INTERVAL  = int(os.getenv("CHECK_INTERVAL", "90"))
RECORD_ON_LIVE  = os.getenv("RECORD_ON_LIVE", "false").lower() == "true"
# ============================

if not TELEGRAM_TOKEN or not CHAT_ID or not TIKTOK_USERS:
    raise SystemExit("Bitte TELEGRAM_TOKEN, CHAT_ID und TIKTOK_USERS als Environment Variablen setzen.")

bot = Bot(token=TELEGRAM_TOKEN)
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})

def notify(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        print("Telegram-Fehler:", e, flush=True)

def is_live(username):
    try:
        html = SESSION.get(f"https://www.tiktok.com/@{username}", timeout=15).text
        return '"isLive":true' in html or '"liveRoomId"' in html
    except Exception:
        return False

def main():
    last = {u: False for u in TIKTOK_USERS}
    notify(f"🚀 TikTok Live Bot gestartet. Überwache: {', '.join('@'+u for u in TIKTOK_USERS)}")
    while True:
        for user in TIKTOK_USERS:
            live = is_live(user)
            if live and not last[user]:
                notify(f"🔴 @{user} ist jetzt LIVE auf TikTok!")
            elif not live and last[user]:
                notify(f"⚪ @{user} ist nicht mehr live.")
            last[user] = live
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    main()

