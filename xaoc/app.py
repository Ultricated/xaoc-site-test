from flask import Flask, render_template, request, jsonify
import subprocess
import os
import sys
import requests

app = Flask(__name__)

bot_process = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def status():
    global bot_process
    if bot_process is not None and bot_process.poll() is None:
        return jsonify({"status": "running"})
    return jsonify({"status": "stopped"})

@app.route('/api/start', methods=['POST'])
def start_bot():
    global bot_process
    data = request.json
    token = data.get('token')

    if not token or len(token) < 20:
        return jsonify({"error": "Invalid token format"}), 400

    # TEST THE TOKEN BEFORE LAUNCHING TO PREVENT UI HANGING
    try:
        headers = {"Authorization": token}
        r = requests.get("https://discord.com/api/v10/users/@me", headers=headers, timeout=5)
        if r.status_code != 200:
            return jsonify({"error": "Invalid Token! Discord rejected it."}), 401
    except Exception:
        return jsonify({"error": "Could not reach Discord to verify token."}), 500

    if bot_process is not None:
        try:
            bot_process.terminate()
            bot_process.wait(timeout=3)
        except Exception:
            pass

    env = os.environ.copy()
    env["TOKEN"] = token

    try:
        # Log bot output to a file so it doesn't deadlock the web server
        log_file = open("bot.log", "a")
        log_file.write("\n--- STARTING BOT ---\n")
        
        bot_process = subprocess.Popen(
            [sys.executable, "main.py"],
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True
        )
        return jsonify({"message": "Connecting..."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    global bot_process
    if bot_process is not None:
        try:
            bot_process.terminate()
            bot_process.wait(timeout=3)
            bot_process = None
            return jsonify({"message": "Offline"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Not running"}), 400

if __name__ == '__main__':
    print("Starting Xaoc Dashboard on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
