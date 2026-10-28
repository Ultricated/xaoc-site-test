import os
import threading
from flask import Flask
import discord

# 1. Web server setup (keeps Render's port check happy)
app = Flask(__name__)

@app.route('/')
def home():
    return "Selfbot is running online!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. Discord Selfbot Setup using discord.py-self
client = discord.Client()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        await message.channel.send('Hello!')

# 3. Execution entry point
if __name__ == '__main__':
    # Start Flask in a background thread so Render's port checker stays happy
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    # Run the selfbot directly with your token
    TOKEN = os.environ.get("DISCORD_TOKEN")
    client.run(TOKEN, bot=False)
