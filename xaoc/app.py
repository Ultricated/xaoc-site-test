from flask import Flask, render_template, request, jsonify
import subprocess
import os
import sys
import requests
import shutil

app = Flask(__name__)

# This dictionary will store all running bots
active_bots = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def status():
    # Clean up dead processes from the list
    dead_ids = []
    for uid, data in active_bots.items():
        if data["process"].poll() is not None:
            dead_ids.append(uid)
    for uid in dead_ids:
        del active_bots[uid]
        
    bots_list = [{"id": uid, "name": data["name"]} for uid, data in active_bots.items()]
    return jsonify({"bots": bots_list})

@app.route('/api/start', methods=['POST'])
def start_bot():
    data = request.json
    token = data.get('token')

    if not token or len(token) < 20:
        return jsonify({"error": "Invalid token format"}), 400

    # 1. Verify token with Discord and get account info
    try:
        headers = {"Authorization": token}
        r = requests.get("https://discord.com/api/v10/users/@me", headers=headers, timeout=5)
        if r.status_code != 200:
            return jsonify({"error": "Invalid Token! Discord rejected it."}), 401
        user_data = r.json()
        user_id = user_data["id"]
        username = user_data.get("username", "Unknown")
    except Exception:
        return jsonify({"error": "Could not reach Discord to verify token."}), 500

    # 2. Check if this token is already running
    if user_id in active_bots:
        return jsonify({"error": f"{username} is already running!"}), 400

    # 3. Create an isolated folder for this specific account
    instance_dir = os.path.join(os.getcwd(), "instances", user_id)
    os.makedirs(instance_dir, exist_ok=True)

    try:
        shutil.copy("main.py", os.path.join(instance_dir, "main.py"))
    except Exception as e:
        return jsonify({"error": f"Failed to copy main.py: {e}"}), 500

    # 4. Start the bot process
    env = os.environ.copy()
    env["TOKEN"] = token

    try:
        log_file = open(os.path.join(instance_dir, "bot.log"), "a")
        log_file.write(f"\n--- STARTING BOT FOR {username} ---\n")
        
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=instance_dir, 
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        active_bots[user_id] = {"process": process, "name": username}
        return jsonify({"message": "Connecting..."})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# The /api/stop route is completely gone. They cannot kill bots from the website.

if __name__ == '__main__':
    print("Starting Xaoc Dashboard on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
