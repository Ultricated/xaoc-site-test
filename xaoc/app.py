from flask import Flask, render_template, request, jsonify
import subprocess
import os
import sys

app = Flask(__name__)

# Keep track of the running bot process
bot_process = None

@app.route('/')
def index():
    # Serves the index.html file from the templates folder
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

    # If the bot is already running, kill it first before starting a new one
    if bot_process is not None:
        try:
            bot_process.terminate()
            bot_process.wait(timeout=3)
        except Exception:
            pass

    # Copy the system environment and securely add the token
    env = os.environ.copy()
    env["TOKEN"] = token

    try:
        # Launch main.py using the same Python executable that is running app.py
        bot_process = subprocess.Popen(
            [sys.executable, "main.py"],
            env=env,
            stdout=subprocess.PIPE,
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
    # Runs the web server
    app.run(host='0.0.0.0', port=5000, debug=False)