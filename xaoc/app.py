<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Xaoc Dashboard</title>
    <style>
        body {
            background-color: #0f0f0f;
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
            margin: 0;
            padding-top: 50px;
        }
        .card {
            background-color: #1a1a1a;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            text-align: center;
            width: 400px;
        }
        h1 { margin: 0 0 10px 0; font-size: 24px; letter-spacing: 1px; }
        .status { color: #00ff00; font-size: 14px; font-weight: bold; margin-bottom: 30px; letter-spacing: 1px; }
        input {
            width: 100%; padding: 12px; background-color: #0a0a0a; border: 1px solid #333;
            border-radius: 6px; color: white; box-sizing: border-box; margin-bottom: 15px; outline: none;
        }
        input:focus { border-color: #555; }
        button.start-btn {
            width: 100%; padding: 12px; background-color: white; color: black; border: none;
            border-radius: 6px; font-weight: bold; font-size: 16px; cursor: pointer; transition: 0.2s;
        }
        button.start-btn:hover { background-color: #ddd; }
        button.start-btn:disabled { background-color: #555; color: #aaa; cursor: not-allowed; }
        
        .msg { margin-top: 15px; font-size: 14px; color: #00ff00; min-height: 20px; }
        .error { color: #ff4444; }
        
        .bot-list { margin-top: 25px; text-align: left; }
        .bot-item {
            display: flex; justify-content: space-between; align-items: center;
            background: #222; padding: 12px 15px; border-radius: 6px; margin-bottom: 10px;
            border-left: 4px solid #00ff00;
        }
        .bot-text { font-weight: bold; font-size: 14px; }
        .stop-btn {
            background: #ff4444; color: white; border: none; padding: 6px 15px;
            border-radius: 4px; cursor: pointer; font-weight: bold; transition: 0.2s;
        }
        .stop-btn:hover { background: #cc0000; }
    </style>
</head>
<body>

<div class="card">
    <h1>Xaoc.</h1>
    <div class="status" id="statusText">0 BOTS ONLINE</div>
    
    <input type="password" id="tokenInput" placeholder="Paste token here...">
    <button onclick="startBot()" id="hostBtn" class="start-btn">Host Selfbot</button>
    
    <div class="msg" id="messageText"></div>

    <!-- This list will show the active bots -->
    <div class="bot-list" id="botList"></div>
</div>

<script>
    setInterval(fetchStatus, 3000);

    async function fetchStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            
            const statusText = document.getElementById('statusText');
            const botList = document.getElementById('botList');
            
            statusText.innerText = data.bots.length + (data.bots.length === 1 ? " BOT ONLINE" : " BOTS ONLINE");
            botList.innerHTML = ""; 
            
            data.bots.forEach(bot => {
                const div = document.createElement('div');
                div.className = 'bot-item';
                
                let actionHtml = "";
                // Only show the stop button if the browser cookie says it belongs to you
                if (bot.mine) {
                    actionHtml = `<button class="stop-btn" onclick="stopBot('${bot.hash}')">Stop</button>`;
                }
                
                let label = bot.mine ? "Your Selfbot" : "Anonymous Selfbot";
                
                div.innerHTML = `
                    <span class="bot-text">${label}</span>
                    ${actionHtml}
                `;
                botList.appendChild(div);
            });
        } catch(e) {}
    }

    async function startBot() {
        const token = document.getElementById('tokenInput').value;
        const msg = document.getElementById('messageText');
        const btn = document.getElementById('hostBtn');
        
        if(!token) {
            msg.innerText = "Please paste a token.";
            msg.className = "msg error";
            return;
        }

        msg.innerText = "Verifying token...";
        msg.className = "msg";
        btn.innerText = "Connecting...";
        btn.disabled = true;

        try {
            const res = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: token })
            });
            
            const data = await res.json();
            
            if(res.ok) {
                msg.innerText = "Connected!";
                msg.className = "msg";
                document.getElementById('tokenInput').value = ""; 
                fetchStatus();
            } else {
                msg.innerText = data.error;
                msg.className = "msg error";
            }
        } catch (e) {
            msg.innerText = "Server error.";
            msg.className = "msg error";
        }
        
        btn.innerText = "Host Selfbot";
        btn.disabled = false;
    }

    async function stopBot(hash) {
        try {
            const res = await fetch('/api/stop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ hash: hash })
            });
            const data = await res.json();
            if (!res.ok) {
                alert(data.error);
            }
            fetchStatus();
        } catch (e) {}
    }
    
    fetchStatus();
</script>

</body>
</html>
