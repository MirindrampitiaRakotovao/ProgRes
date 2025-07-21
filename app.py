from flask import Flask, render_template
import threading
import time

app = Flask(__name__)
LOG_FILE = "logs.txt"

def read_logs():
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return lines[-100:] 
    except FileNotFoundError:
        return []

@app.route("/")
def index():
    logs = read_logs()
    return render_template("index.html", logs=logs)

def run_flask():
    app.run(port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":

    threading.Thread(target=run_flask).start()
