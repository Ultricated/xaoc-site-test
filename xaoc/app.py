from flask import Flask, render_template, request, jsonify, session
import subprocess
import os
import sys
import requests
import shutil
import time
import secrets
import uuid

app = Flask(__name__)
# This secret key keeps the session cookies secure so people can't fake them
app.secret_key = secrets.token_hex(32) 

# Format: { "random_hash": {"process": process, "discord_id": id} }
active_bots = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def status():
    dead_hashes = []
    for bot_hash, data in active_bots.items():
        if data["process"].poll() is not None:
            dead_hashes.append(bot_hash)
    for h in dead_hashes:
        del active_bots[h]
        
    my_bots = session.get('my_bots', [])
    bots_list = []
    
    # We send a random hash instead of the Discord ID
    for bot_hash in active_bots.keys():
        bots_list.append({
            "hash": bot_hash, 
            "mine": bot_hash in my_bots 
        })
        
    return jsonify({"bots": bots_list})

@app.route('/api/start', methods=['POST'])
def start_bot():
    data = request.json
    token = data.get('token')

    if not token or len(token) < 20:
        return jsonify({"error": "Invalid token format"}), 400

    # 1. Verify token with Discord (Token is NEVER sent to the frontend)
    try:
        headers = {"Authorization": token}
        r = requests.get("https://discord.com/api/v10/users/@me", headers=headers, timeout=5)
        if r.status_code != 200:
            return jsonify({"error": "Invalid Token! Discord rejected it."}), 401
        user_data = r.json()
        user_id = user_data["id"]
        username = user_data.get("username", "Unknown")
    except Exception:
        return jsonify({"error": "Could not reach Discord."}), 500

    # Check if this Discord ID is already running
    for data in active_bots.values():
        if data["discord_id"] == user_id:
            return jsonify({"error": "This token is already running!"}), 400

    # 2. Set up folder
    instance_dir = os.path.join(os.getcwd(), "instances", user_id)
    os.makedirs(instance_dir, exist_ok=True)

    if not os.path.exists("main.py"):
        return jsonify({"error": "main.py is missing!"}), 500

    try:
        shutil.copy("main.py", os.path.join(instance_dir, "main.py"))
    except Exception as e:
        return jsonify({"error": f"Failed to copy main.py: {e}"}), 500

    # 3. Start the bot
    env = os.environ.copy()
    env["TOKEN"] = token  # Stored ONLY in server memory, never sent to user
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
        
        time.sleep(3)
        
        if process.poll() is not None:
            with open(log_path, "r") as f:
                logs = f.read()
            error_msg = logs[-300:].replace("\n", " | ")
            return jsonify({"error": f"Bot crashed: {error_msg}"}), 500

        # Generate a random hash to identify this bot securely
        bot_hash = str(uuid.uuid4())
        
        active_bots[bot_hash] = {"process": process, "discord_id": user_id}
        
        my_bots = session.get('my_bots', [])
        if bot_hash not in my_bots:
            my_bots.append(bot_hash)
            session['my_bots'] = my_bots

        return jsonify({"message": "Connected!"})
        
    except Exception as e:
        return jsonify({"error": f"System error: {str(e)}"}), 500

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    data = request.json
    bot_hash = data.get('hash')
    my_bots = session.get('my_bots', [])
    
    # SECURITY: If the hash isn't in your session, you can't stop it
    if bot_hash not in my_bots:
        return jsonify({"error": "You don't own this bot."}), 403
        
    if bot_hash in active_bots:
        try:
            active_bots[bot_hash]["process"].terminate()
            active_bots[bot_hash]["process"].wait(timeout=3)
            del active_bots[bot_hash]
            
            my_bots.remove(bot_hash)
            session['my_bots'] = my_bots
            
            return jsonify({"message": "Offline"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Not running"}), 400

if __name__ == '__main__':
    print("Starting Xaoc Dashboard on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
