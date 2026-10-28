import os
import asyncio
import threading
import uuid
from flask import Flask, render_template, request, jsonify, make_response
from flask_session import Session
import discord
from discord.ext import commands

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Max bots running simultaneously
MAX_CONCURRENT_BOTS = 20 
active_bots = {}
queue = None
bot_loop = None

class FullSelfbot(commands.Bot):
    def __init__(self, token, session_id):
        super().__init__(command_prefix=".", self_bot=True, intents=discord.Intents.all())
        self.token = token
        self.session_id = session_id

    async def on_ready(self):
        print(f"[+] [{self.session_id}] Logged in as {self.user.name}")

async def bot_worker():
    while True:
        token, session_id = await queue.get()
        
        # Check if session was cancelled while in queue
        if session_id not in active_bots:
            queue.task_done()
            continue

        bot = FullSelfbot(token, session_id)
        active_bots[session_id]["bot"] = bot
        
        try:
            await bot.start(token)
        except Exception as e:
            print(f"[-] [{session_id}] Disconnected: {e}")
        finally:
            if session_id in active_bots:
                del active_bots[session_id]
            queue.task_done()

def start_async_loop():
    global bot_loop, queue
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)
    queue = asyncio.Queue()
    
    # Start worker pool
    for _ in range(MAX_CONCURRENT_BOTS):
        bot_loop.create_task(bot_worker())
        
    bot_loop.run_forever()

threading.Thread(target=start_async_loop, daemon=True).start()

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
    
    resp = make_response(jsonify({"message": "Added to queue" if queue.qsize() >= MAX_CONCURRENT_BOTS else "Connecting..."}))
    resp.set_cookie('xaoc_session', session_id, httponly=True, secure=True, samesite='Strict')

    active_bots[session_id] = {"token": token, "status": "queued"}
    asyncio.run_coroutine_threadsafe(queue.put((token, session_id)), bot_loop)

    return resp

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    session_id = request.cookies.get('xaoc_session')
    
    if session_id in active_bots:
        bot = active_bots[session_id].get("bot")
        if bot:
            asyncio.run_coroutine_threadsafe(bot.close(), bot_loop)
            
        del active_bots[session_id]
        
        resp = make_response(jsonify({"message": "Disconnected"}))
        resp.delete_cookie('xaoc_session')
        return resp
        
    return jsonify({"error": "Session not found"}), 400

@app.route('/api/status', methods=['GET'])
def status():
    session_id = request.cookies.get('xaoc_session')
    global_active = len(active_bots)
    if session_id and session_id in active_bots:
        return jsonify({"status": "running", "global": global_active})
    return jsonify({"status": "stopped", "global": global_active})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
