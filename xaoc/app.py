import os
import uuid
import subprocess
import sys
from flask import Flask, render_template, request, jsonify, make_response
from flask_session import Session

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Store all running processes in a dictionary
active_processes = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_bot():
    data = request.json
    token = data.get('token')

    if not token or len(token) < 20:
        return jsonify({"error": "Invalid token format"}), 400

    # Generate a unique ID for this browser session
    session_id = str(uuid.uuid4())
    
    # Pass the token to main.py securely via environment variables
    env = os.environ.copy()
    env["TOKEN"] = token

    try:
        # Launch main.py for this specific token
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        active_processes[session_id] = process
        
        # Set the cookie to identify this user
        resp = make_response(jsonify({"message": "Connecting..."}))
        resp.set_cookie('xaoc_session', session_id, httponly=True, secure=True, samesite='Strict')
        return resp
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    session_id = request.cookies.get('xaoc_session')
    
    if session_id in active_processes:
        proc = active_processes[session_id]
        proc.terminate() # Kill the subprocess
        del active_processes[session_id]
        
        resp = make_response(jsonify({"message": "Disconnected"}))
        resp.delete_cookie('xaoc_session')
        return resp
        
    return jsonify({"error": "Not running"}), 400

@app.route('/api/status', methods=['GET'])
def status():
    session_id = request.cookies.get('xaoc_session')
    
    # Check if the process exists and is still running
    if session_id in active_processes and active_processes[session_id].poll() is None:
        return jsonify({"status": "running", "global": len(active_processes)})
        
    # If it crashed or finished, clean it up
    if session_id in active_processes:
        del active_processes[session_id]
        
    return jsonify({"status": "stopped", "global": len(active_processes)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
