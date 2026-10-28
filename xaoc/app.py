from flask import Flask, render_template, request, jsonify, session
import subprocess
import os
import sys
import requests
import shutil
import time
import secrets

app = Flask(__name__)
# Secret key is required to use secure browser sessions
app.secret_key = secrets.token_hex(32) 

active_bots = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def status():
    # Clean up dead processes
    dead_ids = []
    for uid, data in active_bots.items():
        if data["process"].poll() is not None:
            dead_ids.append(uid)
    for uid in dead_ids:
        del active_bots[uid]
        
    # Check which bots belong to the person viewing the website
    my_bots = session.get('my_bots', [])
    bots_list = []
    
    for uid in active_bots.keys():
        bots_list.append({
            "id": uid, 
            "mine": uid in my_bots # True if this browser started it
        })
        
    return jsonify({"bots": bots_list})

@app.route('/api/start', methods=['POST'])
def start_bot():
    data = request.json
    token = data.get('token')

    if not token or len(token) < 20:
        return jsonify({"error": "Invalid token format"}), 400

    # 1. Verify token
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

    if user_id in active_bots:
        return jsonify({"error": "This token is already running!"}), 400

    # 2. Set up folder
    instance_dir = os.path.join(os.getcwd(), "instances", user_id)
    os.makedirs(instance_dir, exist_ok=True)

    if not os.path.exists("main.py"):
        return jsonify({"error": "main.py is missing from the dashboard folder!"}), 500

    try:
        shutil.copy("main.py", os.path.join(instance_dir, "main.py"))
    except Exception as e:
        return jsonify({"error": f"Failed to copy main.py: {e}"}), 500

    # 3. Start the bot
    env = os.environ.copy()
    env["TOKEN"] = token
    log_path = os.path.join(instance_dir, "bot.log")

    try:
        log_file = open(log_path, "a")
        log_file.write(f"\n\n--- STARTING BOT FOR {username} ---\n")
        
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=instance_dir, 
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # WAIT 3 SECONDS AND CHECK IF IT CRASHED
        time.sleep(3)
        
        if process.poll() is not None:
            with open(log_path, "r") as f:
                logs = f.read()
            error_msg = logs[-300:].replace("\n", " | ")
            return jsonify({"error": f"Bot crashed! Error: {error_msg}"}), 500

        # If we get here, it's alive! Save it to memory and this browser's session
        active_bots[user_id] = {"process": process, "name": username}
        
        my_bots = session.get('my_bots', [])
        if user_id not in my_bots:
            my_bots.append(user_id)
            session['my_bots'] = my_bots

        return jsonify({"message": "Connected!"})
        
    except Exception as e:
        return jsonify({"error": f"System error: {str(e)}"}), 500

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    data = request.json
    user_id = data.get('id')
    my_bots = session.get('my_bots', [])
    
    # SECURITY CHECK: If the bot isn't in your browser's session, you can't stop it
    if user_id not in my_bots:
        return jsonify({"error": "You don't have permission to stop this bot."}), 403
        
    if user_id in active_bots:
        try:
            active_bots[user_id]["process"].terminate()
            active_bots[user_id]["process"].wait(timeout=3)
            del active_bots[user_id]
            
            # Remove from session
            my_bots.remove(user_id)
            session['my_bots'] = my_bots
            
            return jsonify({"message": "Offline"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Not running"}), 400

if __name__ == '__main__':
    print("Starting Xaoc Dashboard on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
