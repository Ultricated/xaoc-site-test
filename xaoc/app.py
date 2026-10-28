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

active_processes = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_bot():
    data = request.json
    token = data.get('token')

    if not token or len(token) < 50 or token.count('.') != 2:
        return jsonify({"error": "Invalid token format"}), 400

    session_id = str(uuid.uuid4())
    
    # Pass the token to main.py
    env = os.environ.copy()
    env["TOKEN"] = token

    try:
        # Run main.py directly. No stdout pipes to prevent deadlocks.
        process = subprocess.Popen(
            ["python", "main.py"],
            env=env
        )
        active_processes[session_id] = process
        
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
        proc.terminate() # Kills the main.py process
        del active_processes[session_id]
        
        resp = make_response(jsonify({"message": "Disconnected"}))
        resp.delete_cookie('xaoc_session')
        return resp
        
    return jsonify({"error": "Not running"}), 400

@app.route('/api/status', methods=['GET'])
def status():
    session_id = request.cookies.get('xaoc_session')
    
    if session_id in active_processes and active_processes[session_id].poll() is None:
        return jsonify({"status": "running", "global": len(active_processes)})
        
    if session_id in active_processes:
        del active_processes[session_id]
        
    return jsonify({"status": "stopped", "global": len(active_processes)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
