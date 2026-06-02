from fastapi.responses import HTMLResponse

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SECURE ACCESS | Vexylo Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #020617;
            --surface: rgba(2, 6, 23, 0.8);
            --cyan: #00f0ff;
            --cyan-dim: rgba(0, 240, 255, 0.2);
            --orange: #f97316;
            --text-main: #e2e8f0;
            --text-sec: #64748b;
        }
        body {
            margin: 0; padding: 0; background-color: var(--bg);
            color: var(--text-main); font-family: 'Share Tech Mono', monospace;
            display: flex; justify-content: center; align-items: center;
            height: 100vh; overflow: hidden;
            background-image: 
                linear-gradient(var(--cyan-dim) 1px, transparent 1px),
                linear-gradient(90deg, var(--cyan-dim) 1px, transparent 1px);
            background-size: 40px 40px;
            background-position: center center;
        }
        body::before {
            content: ''; position: absolute; top:0; left:0; right:0; bottom:0;
            background: radial-gradient(circle, transparent 20%, var(--bg) 90%);
            pointer-events: none;
        }
        .crosshair { position: absolute; width: 20px; height: 20px; border: 1px solid var(--cyan); pointer-events:none; z-index: 100;}
        .ch-tl { top: 30px; left: 30px; border-right: none; border-bottom: none; }
        .ch-tr { top: 30px; right: 30px; border-left: none; border-bottom: none; }
        .ch-bl { bottom: 30px; left: 30px; border-right: none; border-top: none; }
        .ch-br { bottom: 30px; right: 30px; border-left: none; border-top: none; }
        
        .login-vault {
            position: relative; z-index: 10;
            background: var(--surface);
            border: 1px solid var(--cyan);
            padding: 40px; width: 400px;
            backdrop-filter: blur(10px);
            box-shadow: 0 0 30px var(--cyan-dim), inset 0 0 20px var(--cyan-dim);
            clip-path: polygon(0 15px, 15px 0, 100% 0, 100% calc(100% - 15px), calc(100% - 15px) 100%, 0 100%);
        }
        .login-vault::after {
            content: 'SYS.AUTH.REQ'; position: absolute; top: 5px; right: 15px; font-size: 10px; color: var(--cyan); letter-spacing: 2px;
        }
        h2 {
            text-align: center; color: var(--cyan); font-size: 22px; letter-spacing: 4px;
            margin-bottom: 30px; text-transform: uppercase; text-shadow: 0 0 10px var(--cyan);
        }
        .input-group { margin-bottom: 25px; position: relative; }
        .input-group label {
            display: block; font-size: 12px; color: var(--text-sec); margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px;
        }
        .input-group input {
            width: 100%; padding: 12px; background: rgba(0,0,0,0.5);
            border: 1px solid var(--text-sec); color: var(--cyan);
            font-family: 'Share Tech Mono', monospace; font-size: 16px;
            outline: none; transition: 0.3s; box-sizing: border-box;
        }
        .input-group input:focus { border-color: var(--cyan); box-shadow: inset 0 0 10px var(--cyan-dim); }
        
        /* Typing animation line */
        .input-group input:focus + .loading-line {
            position: absolute; bottom: 0; left: 0; height: 2px; background: var(--cyan);
            animation: loadLine 1s infinite alternate;
        }
        @keyframes loadLine { 0% { width: 0%; } 100% { width: 100%; } }
        
        button {
            width: 100%; padding: 15px; background: transparent;
            border: 1px solid var(--cyan); color: var(--cyan);
            font-family: 'Share Tech Mono', monospace; font-size: 16px;
            text-transform: uppercase; letter-spacing: 2px; cursor: pointer;
            position: relative; overflow: hidden; transition: 0.3s;
            clip-path: polygon(0 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%);
        }
        button:hover { background: var(--cyan-dim); text-shadow: 0 0 5px var(--cyan); }
        button::before {
            content: ''; position: absolute; top: 0; left: -100%; width: 50%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0,240,255,0.4), transparent);
            transform: skewX(-20deg); transition: 0s;
        }
        button:hover::before { left: 150%; transition: 0.8s ease-in-out; }
        
        #error-msg { color: var(--orange); text-align: center; margin-top: 15px; font-size: 14px; min-height: 20px; text-shadow: 0 0 5px var(--orange); }
        
        .coords { position: absolute; font-size: 10px; color: var(--text-sec); letter-spacing: 1px; top: 45px; left: 20px; }
    </style>
</head>
<body>
    <div class="crosshair ch-tl"></div>
    <div class="crosshair ch-tr"></div>
    <div class="crosshair ch-bl"></div>
    <div class="crosshair ch-br"></div>
    <div class="coords">LAT 40.7128 N<br>LON 74.0060 W</div>
    
    <div class="login-vault">
        <h2>VEXYLO DASHBOARD</h2>
        <form id="loginForm">
            <div class="input-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
                <div class="loading-line"></div>
            </div>
            <div class="input-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
                <div class="loading-line"></div>
            </div>
            <button type="submit">INICIAR SESSÃO</button>
        </form>
        <div id="error-msg"></div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const errorMsg = document.getElementById('error-msg');
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    window.location.href = '/api';
                } else {
                    errorMsg.textContent = 'ACCESS DENIED: Invalid Credentials';
                    document.body.style.transform = 'translate(4px, 2px)';
                    setTimeout(() => document.body.style.transform = 'translate(-2px, -4px)', 50);
                    setTimeout(() => document.body.style.transform = 'translate(0, 0)', 100);
                }
            } catch (err) {
                errorMsg.textContent = 'SYSTEM ERROR: Connection Failed';
            }
        });
    </script>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VEXYLO TACTICAL UI</title>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #020617;
            --surface: rgba(2, 6, 23, 0.85);
            --cyan: #00f0ff;
            --cyan-dim: rgba(0, 240, 255, 0.2);
            --orange: #f97316;
            --text-main: #e2e8f0;
            --text-sec: #64748b;
        }
        body {
            margin: 0; padding: 0; background-color: var(--bg);
            color: var(--text-main); font-family: 'Share Tech Mono', monospace;
            display: flex; flex-direction: column; align-items: center;
            height: 100vh; overflow: hidden;
        }
        .grid-bg {
            position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: -1;
            background-image: 
                linear-gradient(var(--cyan-dim) 1px, transparent 1px),
                linear-gradient(90deg, var(--cyan-dim) 1px, transparent 1px);
            background-size: 50px 50px; opacity: 0.3;
        }
        
        .container {
            width: 100%; max-width: 1400px; margin: 20px auto; display: flex; flex-direction: column; height: calc(100vh - 40px);
        }
        
        /* Header */
        .tactical-header {
            display: flex; justify-content: space-between; align-items: center;
            border: 1px solid var(--cyan); background: var(--surface); padding: 15px 25px;
            backdrop-filter: blur(10px); margin-bottom: 20px;
            clip-path: polygon(0 0, 100% 0, 100% calc(100% - 15px), calc(100% - 15px) 100%, 0 100%);
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
        }
        .os-log { display: flex; align-items: center; gap: 15px; color: var(--cyan); font-size: 16px; letter-spacing: 2px; font-weight: bold;}
        .radar { width: 14px; height: 14px; background: var(--cyan); border-radius: 50%; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 240, 255, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(0, 240, 255, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 240, 255, 0); } }
        
        .header-actions { display: flex; gap: 15px; }
        .header-actions a, .header-actions button {
            color: var(--cyan); text-decoration: none; font-size: 12px; border: 1px solid var(--cyan); padding: 8px 15px; background: transparent; cursor:pointer; text-transform: uppercase; font-family: 'Share Tech Mono', monospace; transition: 0.2s;
        }
        .header-actions a:hover { background: var(--cyan-dim); }
        .header-actions button.logout { border-color: var(--orange); color: var(--orange); }
        .header-actions button.logout:hover { background: rgba(249, 115, 22, 0.2); }
        
        /* Tabs Nav */
        .tabs-nav { display: flex; gap: 15px; margin-bottom: 20px; }
        .tab-btn {
            background: var(--surface); border: 1px solid var(--text-sec); color: var(--text-sec);
            padding: 12px 25px; cursor: pointer; font-family: 'Share Tech Mono', monospace; font-size: 14px;
            letter-spacing: 2px; text-transform: uppercase; transition: 0.3s;
            clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
        }
        .tab-btn:hover { border-color: var(--cyan); color: var(--text-main); }
        .tab-btn.active { background: var(--cyan-dim); border-color: var(--cyan); color: var(--cyan); box-shadow: inset 0 0 10px var(--cyan-dim); }
        
        /* Panel Content */
        .panel {
            flex-grow: 1; background: var(--surface); border: 1px solid var(--cyan); padding: 30px;
            backdrop-filter: blur(10px); overflow-y: auto; position: relative;
            clip-path: polygon(0 0, calc(100% - 20px) 0, 100% 20px, 100% 100%, 20px 100%, 0 calc(100% - 20px));
        }
        .panel::-webkit-scrollbar { width: 4px; }
        .panel::-webkit-scrollbar-thumb { background: var(--cyan); }
        
        .tab-content { display: none; }
        .tab-content.active { display: block; animation: scanline 0.4s ease-out forwards; }
        @keyframes scanline { 0% { clip-path: inset(0 100% 0 0); } 100% { clip-path: inset(0 0 0 0); } }
        
        h2 { color: var(--cyan); font-size: 20px; margin-bottom: 25px; text-transform: uppercase; border-bottom: 1px solid var(--cyan-dim); padding-bottom: 10px; display: inline-block; padding-right: 50px; }
        
        /* Tactical Tables */
        table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }
        th { color: var(--cyan); text-align: left; padding: 12px; border-bottom: 1px solid var(--cyan); text-transform: uppercase; letter-spacing: 1px; }
        td { padding: 12px; border-bottom: 1px solid var(--text-sec); color: var(--text-main); }
        tr:hover td { background: rgba(0, 240, 255, 0.05); }
        
        /* Badges */
        .badge { padding: 3px 8px; border: 1px solid; font-size: 11px; margin-right: 5px; border-radius: 2px; }
        .badge.cyan { color: var(--cyan); border-color: var(--cyan); background: rgba(0, 240, 255, 0.1); }
        .badge.orange { color: var(--orange); border-color: var(--orange); background: rgba(249, 115, 22, 0.1); font-weight: bold;}
        
        /* Switches (Checkboxes) */
        .switch-container { display: flex; gap: 20px; margin-bottom: 25px; flex-wrap: wrap; background: rgba(0,0,0,0.3); padding: 15px; border: 1px solid var(--cyan-dim); border-left: 3px solid var(--cyan); }
        .switch-label {
            display: flex; align-items: center; gap: 10px; cursor: pointer; color: var(--text-sec); font-size: 13px; text-transform: uppercase; letter-spacing: 1px;
        }
        .switch-label:hover { color: var(--text-main); }
        .switch-label input[type="checkbox"] {
            appearance: none; width: 36px; height: 18px; background: rgba(0,0,0,0.5); border: 1px solid var(--text-sec);
            position: relative; outline: none; cursor: pointer; border-radius: 9px;
        }
        .switch-label input[type="checkbox"]::before {
            content: ''; position: absolute; width: 12px; height: 12px; background: var(--text-sec); top: 2px; left: 2px; border-radius: 50%; transition: 0.2s;
        }
        .switch-label input[type="checkbox"]:checked { border-color: var(--cyan); background: rgba(0, 240, 255, 0.2); }
        .switch-label input[type="checkbox"]:checked::before { background: var(--cyan); left: 20px; box-shadow: 0 0 8px var(--cyan); }
        
        .switch-label.admin input[type="checkbox"]:checked { border-color: var(--orange); background: rgba(249, 115, 22, 0.2); }
        .switch-label.admin input[type="checkbox"]:checked::before { background: var(--orange); box-shadow: 0 0 8px var(--orange); }
        .switch-label.admin strong { color: var(--orange); }
        
        /* Buttons */
        .btn {
            background: transparent; border: 1px solid var(--cyan); color: var(--cyan); padding: 10px 20px; font-family: 'Share Tech Mono', monospace;
            text-transform: uppercase; cursor: pointer; font-size: 13px; clip-path: polygon(0 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%);
            transition: 0.2s; letter-spacing: 1px;
        }
        .btn:hover { background: var(--cyan-dim); box-shadow: 0 0 10px var(--cyan-dim); }
        .btn.danger { border-color: var(--orange); color: var(--orange); }
        .btn.danger:hover { background: rgba(249, 115, 22, 0.2); box-shadow: 0 0 10px rgba(249, 115, 22, 0.3); }
        
        /* Inputs */
        .input-box {
            width: 100%; max-width: 400px; padding: 12px; background: rgba(0,0,0,0.5); border: 1px solid var(--text-sec); color: var(--cyan); font-family: 'Share Tech Mono', monospace; outline:none; margin-bottom: 15px; font-size: 14px;
        }
        .input-box:focus { border-color: var(--cyan); box-shadow: inset 0 0 10px var(--cyan-dim); }
        .input-label { display: block; font-size: 12px; color: var(--text-sec); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
        
        .data-card { border: 1px solid var(--cyan-dim); padding: 15px; background: rgba(0,0,0,0.4); margin-bottom: 15px; border-left: 3px solid var(--cyan); }
        .data-card pre { margin:0; color: var(--text-main); font-size: 13px; white-space: pre-wrap; font-family: 'Share Tech Mono', monospace; }
        
        .toast { position: fixed; bottom: 30px; right: 30px; background: var(--surface); border: 1px solid var(--cyan); padding: 15px 25px; color: var(--cyan); border-left: 4px solid var(--cyan); display: none; z-index: 1000; box-shadow: 0 0 20px var(--cyan-dim); font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
        
        .diag-text { position: absolute; right: 10px; bottom: 10px; font-size: 10px; color: var(--text-sec); text-align: right; pointer-events: none; }
        
        /* Tactical Side Panel (Drawer) */
        .side-panel {
            position: fixed; right: -450px; top: 0; width: 450px; height: 100vh;
            background: rgba(2, 6, 23, 0.95); border-left: 1px solid var(--cyan);
            backdrop-filter: blur(10px); z-index: 2000; box-shadow: -10px 0 30px var(--cyan-dim);
            transition: right 0.4s ease-in-out; display: flex; flex-direction: column;
        }
        .side-panel.open {
            right: 0;
        }
        .panel-header {
            display: flex; justify-content: space-between; align-items: center;
            padding: 20px; border-bottom: 1px solid var(--cyan-dim); background: rgba(0, 240, 255, 0.05);
        }
        .panel-title { color: var(--cyan); font-size: 18px; letter-spacing: 2px; text-transform: uppercase; }
        .close-btn {
            color: var(--orange); cursor: pointer; font-size: 14px; font-weight: bold; border: 1px solid var(--orange);
            padding: 5px 10px; transition: 0.2s; background: transparent; text-transform: uppercase; font-family: 'Share Tech Mono', monospace;
        }
        .close-btn:hover { background: rgba(249, 115, 22, 0.2); box-shadow: 0 0 10px rgba(249, 115, 22, 0.4); }
        .panel-body { padding: 20px; overflow-y: auto; flex-grow: 1; }
        .panel-body::-webkit-scrollbar { width: 4px; }
        .panel-body::-webkit-scrollbar-thumb { background: var(--cyan); }
        
        /* Formatted Data Cards */
        .intel-card {
            border: 1px solid var(--cyan-dim); background: rgba(0,0,0,0.4); padding: 15px; margin-bottom: 15px;
            border-left: 3px solid var(--cyan); display: flex; flex-direction: column; gap: 8px;
        }
        .intel-title { color: var(--cyan); font-size: 16px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px;}
        .intel-field { font-size: 13px; }
        .intel-field span { color: var(--text-sec); text-transform: uppercase; display: inline-block; width: 120px; }
        .intel-field span.intel-value { color: var(--text-main); width: auto; }
        
        .log-box {
            border: 1px solid var(--text-sec); background: rgba(0,0,0,0.3); padding: 12px; margin-bottom: 10px; border-left: 2px solid var(--text-sec);
        }
        .log-time { color: var(--cyan); font-size: 11px; margin-bottom: 5px; }
        .log-content { color: var(--text-main); font-size: 13px; }
    </style>
</head>
<body>
    <div class="grid-bg"></div>
    <div class="container">
        
        <div class="tactical-header">
            <div class="os-log">
                <div class="radar"></div>
                <span id="os-header-text">HOST DETECTED: AWAITING UPLINK</span>
            </div>
            <div class="header-actions">
                <a href="/api/docs" target="_blank">[ OPEN SWAGGER UI ]</a>
                <button class="logout" onclick="logout()">DISCONNECT</button>
            </div>
        </div>

        <div class="tabs-nav">
            <div class="tab-btn active" onclick="switchTab('dashboard', this)">[ 01 // DASHBOARD ]</div>
            <div class="tab-btn" onclick="switchTab('keys', this)">[ 02 // SECURITY & KEYS ]</div>
            <div class="tab-btn" onclick="switchTab('settings', this)">[ 03 // SYSTEM SETTINGS ]</div>
        </div>

        <div class="panel">
            <div class="diag-text">SYS.MEM: OK<br>NET.UPLINK: STABLE<br>ENC: AES-256</div>
            
            <!-- TAB 1: DASHBOARD -->
            <div id="tab-dashboard" class="tab-content active">
                <h2>SYSTEM MONITOR</h2>
                <div class="data-card" id="os-info-card" style="margin-bottom: 30px;">
                    <span style="color:var(--text-sec)">Scanning OS Signature...</span>
                </div>
                
                <h2>MODULE: DOSSIERS</h2>
                <div style="margin-bottom: 30px;">
                    <form id="dossierForm" onsubmit="createDossier(event)" style="display:flex; flex-wrap:wrap; gap: 10px; margin-bottom: 15px; background: rgba(0,0,0,0.3); padding: 15px; border-left: 3px solid var(--cyan);">
                        <input type="text" id="d_name" class="input-box" placeholder="Name" required style="width: 150px; margin:0;">
                        <input type="text" id="d_class" class="input-box" placeholder="Classification" required style="width: 150px; margin:0;">
                        <input type="text" id="d_threat" class="input-box" placeholder="Threat Level" required style="width: 150px; margin:0;">
                        <input type="text" id="d_role" class="input-box" placeholder="Role" required style="width: 150px; margin:0;">
                        <input type="text" id="d_str" class="input-box" placeholder="Strengths" required style="width: 150px; margin:0;">
                        <input type="text" id="d_weak" class="input-box" placeholder="Weaknesses" required style="width: 150px; margin:0;">
                        <input type="text" id="d_notes" class="input-box" placeholder="Notes" style="width: 150px; margin:0;">
                        <button type="submit" class="btn">CREATE DOSSIER</button>
                    </form>
                    <button class="btn" onclick="fetchData('dossiers')">SCAN DOSSIERS</button>
                </div>
                
                <h2>MODULE: SCRATCHPAD</h2>
                <div style="margin-bottom: 30px;">
                    <form id="noteForm" onsubmit="createNote(event)" style="display:flex; gap: 10px; margin-bottom: 15px; background: rgba(0,0,0,0.3); padding: 15px; border-left: 3px solid var(--cyan);">
                        <input type="text" id="n_title" class="input-box" placeholder="Title" required style="width: 200px; margin:0;">
                        <input type="text" id="n_content" class="input-box" placeholder="Content" required style="flex-grow: 1; max-width: none; margin:0;">
                        <button type="submit" class="btn">LOG NOTE</button>
                    </form>
                    <button class="btn" onclick="fetchData('notes')">SCAN NOTES</button>
                </div>
                
                <h2>MODULE: UTILITY BELT</h2>
                <div style="margin-bottom: 30px;">
                    <form id="shortcutForm" onsubmit="createShortcut(event)" style="display:flex; gap: 10px; margin-bottom: 15px; background: rgba(0,0,0,0.3); padding: 15px; border-left: 3px solid var(--cyan);">
                        <input type="text" id="s_name" class="input-box" placeholder="Name" required style="width: 150px; margin:0;">
                        <input type="text" id="s_cmd" class="input-box" placeholder="Command" required style="flex-grow: 1; max-width: none; margin:0;">
                        <input type="text" id="s_desc" class="input-box" placeholder="Description" style="width: 200px; margin:0;">
                        <button type="submit" class="btn">ADD SHORTCUT</button>
                    </form>
                    <button class="btn" onclick="fetchData('shortcuts')">SCAN SHORTCUTS</button>
                </div>
            </div>

            <!-- TAB 2: API KEYS -->
            <div id="tab-keys" class="tab-content">
                <h2>SECURITY & KEYS</h2>
                
                <div style="margin-bottom: 40px;">
                    <label class="input-label">Key Name / Identifier</label>
                    <input type="text" id="key_name" class="input-box" placeholder="e.g. ALPHA-SCRIPT-01">
                    
                    <div class="switch-container">
                        <label class="switch-label admin">
                            <input type="checkbox" id="allow_admin">
                            <strong>TOTAL ADMIN</strong>
                        </label>
                        <div style="width: 2px; background: var(--text-sec); opacity: 0.3; margin: 0 10px;"></div>
                        <label class="switch-label">
                            <input type="checkbox" id="allow_get" checked> LER (GET)
                        </label>
                        <label class="switch-label">
                            <input type="checkbox" id="allow_post"> CRIAR (POST)
                        </label>
                        <label class="switch-label">
                            <input type="checkbox" id="allow_put"> MODIFICAR (PUT)
                        </label>
                        <label class="switch-label">
                            <input type="checkbox" id="allow_delete"> APAGAR (DEL)
                        </label>
                    </div>
                    
                    <button class="btn" onclick="generateKey()">INITIALIZE KEY</button>
                    
                    <div id="new-key-container" style="display: none; margin-top: 20px; align-items: center; gap: 15px;">
                        <input type="text" id="new_key_value" class="input-box" style="margin:0; flex-grow:0; width: 350px;" readonly>
                        <button class="btn" onclick="copyKey()">COPY TO CLIPBOARD</button>
                    </div>
                </div>

                <h2>ACTIVE CLEARANCES</h2>
                <table>
                    <thead>
                        <tr>
                            <th>IDENTIFIER</th>
                            <th>TIMESTAMP</th>
                            <th>ACCESS LEVEL</th>
                            <th>TERMINATE</th>
                        </tr>
                    </thead>
                    <tbody id="keys-table-body">
                        <!-- Keys loaded here -->
                    </tbody>
                </table>
            </div>

            <!-- TAB 3: SETTINGS -->
            <div id="tab-settings" class="tab-content">
                <h2>SYSTEM SETTINGS</h2>
                <p style="color: var(--text-sec); margin-bottom: 25px;">Override master credentials for the current session.</p>
                <form id="credsForm" onsubmit="updateCredentials(event)">
                    <label class="input-label">NEW DIRECTIVE (USERNAME)</label>
                    <input type="text" id="new_user" class="input-box" required>
                    
                    <label class="input-label">NEW CIPHER (PASSWORD)</label>
                    <input type="password" id="new_pass" class="input-box" required>
                    
                    <button type="submit" class="btn">OVERRIDE PROTOCOL</button>
                </form>
            </div>
            
        </div>
    </div>
    
    <!-- TACTICAL SIDE PANEL (DRAWER) -->
    <div id="tactical-side-panel" class="side-panel">
        <div class="panel-header">
            <div class="panel-title" id="panel-title">SCAN RESULTS</div>
            <button class="close-btn" onclick="closePanel()">[ COLLAPSE TERMINAL ]</button>
        </div>
        <div class="panel-body" id="panel-body-content">
            <!-- Data injected here -->
        </div>
    </div>
    
    <div id="toast" class="toast">ACTION SUCCESSFUL</div>

    <script>
        function closePanel() {
            document.getElementById('tactical-side-panel').classList.remove('open');
        }

        function switchTab(tabId, element) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(l => l.classList.remove('active'));
            document.getElementById('tab-' + tabId).classList.add('active');
            if(element) element.classList.add('active');
            
            if (tabId === 'keys') loadKeys();
            if (tabId === 'dashboard') loadOsInfo();
        }

        function showToast(msg) {
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.style.display = 'block';
            setTimeout(() => toast.style.display = 'none', 3000);
        }

        async function logout() {
            try {
                await fetch('/api/logout', { method: 'POST' });
                window.location.href = '/';
            } catch (e) {
                console.error("Logout failed");
            }
        }

        async function loadOsInfo() {
            try {
                const res = await fetch('/api/system/os');
                const data = await res.json();
                
                const osName = data.os !== "Pending Frontend Registration..." ? data.os : "UNKNOWN";
                document.getElementById('os-header-text').textContent = "HOST DETECTED: " + osName.toUpperCase();
                
                document.getElementById('os-info-card').innerHTML = `
                    <span style="color:var(--text-sec)">> SYS.OS:</span> <span style="color:var(--cyan)">${data.os}</span><br>
                    <span style="color:var(--text-sec)">> SYS.DISTRO:</span> <span style="color:var(--cyan)">${data.distro}</span><br>
                    <span style="color:var(--text-sec)">> SYS.PKG:</span> <span style="color:var(--cyan)">${data.package_manager}</span>
                `;
            } catch (e) {
                console.error("Failed to load OS info");
            }
        }

        async function fetchData(endpoint) {
            showToast('INITIATING SCAN: ' + endpoint.toUpperCase());
            try {
                const res = await fetch('/api/' + endpoint);
                const data = await res.json();
                
                const sidePanel = document.getElementById('tactical-side-panel');
                const title = document.getElementById('panel-title');
                const body = document.getElementById('panel-body-content');
                
                title.textContent = "INTEL: " + endpoint.toUpperCase();
                sidePanel.classList.add('open');
                
                if (data.length === 0) {
                    body.innerHTML = '<p style="color: var(--text-sec);">NO RECORDS FOUND IN DATABANKS.</p>';
                    return;
                }
                
                let html = '';
                if (endpoint === 'dossiers') {
                    data.forEach(item => {
                        html += `
                        <div class="intel-card" id="dossier-card-${item.id}">
                            <div class="intel-title">${item.name || 'UNKNOWN TARGET'}</div>
                            <div class="intel-field"><span>CLASS:</span> <input type="text" class="input-box" id="d_class_${item.id}" value="${item.classification || ''}" style="margin:0; padding:4px; font-size:11px; max-width: 150px;"></div>
                            <div class="intel-field"><span>ROLE:</span> <input type="text" class="input-box" id="d_role_${item.id}" value="${item.role || ''}" style="margin:0; padding:4px; font-size:11px; max-width: 150px;"></div>
                            <div class="intel-field"><span>THREAT LEVEL:</span> <input type="text" class="input-box" id="d_threat_${item.id}" value="${item.threat_level || ''}" style="margin:0; padding:4px; font-size:11px; max-width: 150px;"></div>
                            <div class="intel-field"><span>STRENGTHS:</span> <input type="text" class="input-box" id="d_str_${item.id}" value="${item.strengths || ''}" style="margin:0; padding:4px; font-size:11px; max-width: 150px;"></div>
                            <div class="intel-field"><span>WEAKNESSES:</span> <input type="text" class="input-box" id="d_weak_${item.id}" value="${item.weaknesses || ''}" style="margin:0; padding:4px; font-size:11px; max-width: 150px;"></div>
                            <div class="intel-field"><span>NOTES:</span> <input type="text" class="input-box" id="d_notes_${item.id}" value="${item.notes || ''}" style="margin:0; padding:4px; font-size:11px; max-width: 150px;"></div>
                            <div style="margin-top: 10px; display:flex; gap:10px;">
                                <button class="btn" onclick="updateDossier(${item.id}, '${item.name}')">UPDATE INTEL</button>
                                <button class="btn danger" onclick="deleteItem('dossiers', ${item.id})">TERMINATE</button>
                            </div>
                        </div>`;
                    });
                } else if (endpoint === 'notes') {
                    data.forEach(item => {
                        html += `
                        <div class="log-box" style="display:flex; justify-content:space-between; align-items:flex-start;">
                            <div>
                                <div class="log-time">[ ${item.timestamp ? new Date(item.timestamp).toLocaleString() : 'UNKNOWN TIMESTAMP'} ] - ${item.title || ''}</div>
                                <div class="log-content">${item.content || 'Log entry'}</div>
                            </div>
                            <button class="btn danger" style="padding:4px 8px; font-size:10px;" onclick="deleteItem('notes', ${item.id})">DEL</button>
                        </div>`;
                    });
                } else if (endpoint === 'shortcuts') {
                    data.forEach(item => {
                        html += `
                        <div class="log-box" style="display:flex; justify-content:space-between; align-items:flex-start;">
                            <div>
                                <div class="log-time">[ SHORTCUT ] ${item.name || 'UNNAMED'} - ${item.description || ''}</div>
                                <div class="log-content">CMD/URL: ${item.command || 'N/A'}</div>
                            </div>
                            <button class="btn danger" style="padding:4px 8px; font-size:10px;" onclick="deleteItem('shortcuts', ${item.id})">DEL</button>
                        </div>`;
                    });
                } else {
                    data.forEach(item => {
                        html += '<div class="data-card"><pre>' + JSON.stringify(item, null, 2) + '</pre></div>';
                    });
                }
                body.innerHTML = html;
            } catch (e) {
                showToast('ERR: CONNECTION REFUSED');
            }
        }

        async function createDossier(e) {
            e.preventDefault();
            const payload = {
                name: document.getElementById('d_name').value,
                classification: document.getElementById('d_class').value,
                threat_level: document.getElementById('d_threat').value,
                role: document.getElementById('d_role').value,
                strengths: document.getElementById('d_str').value,
                weaknesses: document.getElementById('d_weak').value,
                notes: document.getElementById('d_notes').value
            };
            await postData('dossiers', payload);
            e.target.reset();
        }

        async function updateDossier(id, name) {
            const payload = {
                name: name,
                classification: document.getElementById('d_class_'+id).value,
                threat_level: document.getElementById('d_threat_'+id).value,
                role: document.getElementById('d_role_'+id).value,
                strengths: document.getElementById('d_str_'+id).value,
                weaknesses: document.getElementById('d_weak_'+id).value,
                notes: document.getElementById('d_notes_'+id).value
            };
            try {
                const res = await fetch('/api/dossiers/' + id, {
                    method: 'PUT', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                if(res.ok) { showToast('INTEL UPDATED'); fetchData('dossiers'); }
            } catch(e) { showToast('ERR: UPDATE FAILED'); }
        }

        async function createNote(e) {
            e.preventDefault();
            const payload = { title: document.getElementById('n_title').value, content: document.getElementById('n_content').value };
            await postData('notes', payload);
            e.target.reset();
        }

        async function createShortcut(e) {
            e.preventDefault();
            const payload = { name: document.getElementById('s_name').value, command: document.getElementById('s_cmd').value, description: document.getElementById('s_desc').value };
            await postData('shortcuts', payload);
            e.target.reset();
        }

        async function postData(endpoint, payload) {
            try {
                const res = await fetch('/api/' + endpoint, {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                if(res.ok) { showToast('DATA LOGGED'); fetchData(endpoint); }
                else showToast('ERR: INSERT FAILED');
            } catch(e) { showToast('ERR: CONNECTION FAILED'); }
        }

        async function deleteItem(endpoint, id) {
            if(!confirm('CONFIRM TERMINATION?')) return;
            try {
                const res = await fetch('/api/' + endpoint + '/' + id, { method: 'DELETE' });
                if(res.ok) { showToast('TERMINATED'); fetchData(endpoint); }
            } catch(e) { showToast('ERR: DELETE FAILED'); }
        }

        async function updateCredentials(e) {
            e.preventDefault();
            const user = document.getElementById('new_user').value;
            const pass = document.getElementById('new_pass').value;
            
            try {
                const res = await fetch('/api/settings/update-credentials', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: user, password: pass })
                });
                
                if (res.ok) {
                    showToast('PROTOCOL OVERRIDDEN. REBOOTING...');
                    setTimeout(() => logout(), 2000);
                } else {
                    showToast('ERR: OVERRIDE FAILED.');
                }
            } catch (err) {
                console.error(err);
            }
        }

        async function loadKeys() {
            const tbody = document.getElementById('keys-table-body');
            tbody.innerHTML = '<tr><td colspan="4" style="color:var(--cyan)">Scanning database...</td></tr>';
            try {
                const res = await fetch('/api/keys');
                const keys = await res.json();
                tbody.innerHTML = '';
                if(keys.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" style="color:var(--text-sec)">No active clearances found.</td></tr>';
                    return;
                }
                keys.forEach(k => {
                    const d = new Date(k.created_at).toLocaleString();
                    let perms = '';
                    if(k.allow_admin) {
                        perms = '<span class="badge orange">ADMIN (ALL ACCESS)</span>';
                    } else {
                        if(k.allow_get) perms += '<span class="badge cyan">GET</span>';
                        if(k.allow_post) perms += '<span class="badge cyan">POST</span>';
                        if(k.allow_put) perms += '<span class="badge cyan">PUT</span>';
                        if(k.allow_delete) perms += '<span class="badge cyan">DEL</span>';
                    }
                    
                    tbody.innerHTML += `
                        <tr>
                            <td>${k.name}</td>
                            <td style="color: var(--text-sec); font-size: 12px;">${d}</td>
                            <td>${perms}</td>
                            <td><button class="btn danger" onclick="revokeKey(${k.id})" style="padding: 5px 10px; font-size: 11px;">REVOKE</button></td>
                        </tr>
                    `;
                });
            } catch (e) {
                tbody.innerHTML = '<tr><td colspan="4" style="color: var(--orange);">ERR: DB Access failed.</td></tr>';
            }
        }

        async function generateKey() {
            const name = document.getElementById('key_name').value || 'UNNAMED-KEY';
            const allow_admin = document.getElementById('allow_admin').checked;
            const allow_get = document.getElementById('allow_get').checked;
            const allow_post = document.getElementById('allow_post').checked;
            const allow_put = document.getElementById('allow_put').checked;
            const allow_delete = document.getElementById('allow_delete').checked;
            
            try {
                const res = await fetch('/api/keys', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        name: name,
                        allow_get: allow_get,
                        allow_post: allow_post,
                        allow_put: allow_put,
                        allow_delete: allow_delete,
                        allow_admin: allow_admin
                    })
                });
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('new-key-container').style.display = 'flex';
                    document.getElementById('new_key_value').value = data.key_value;
                    document.getElementById('key_name').value = '';
                    loadKeys();
                    showToast('NEW CLEARANCE GRANTED');
                }
            } catch (e) {
                console.error("Failed to generate key", e);
            }
        }

        async function revokeKey(id) {
            if(!confirm('TERMINATE THIS CLEARANCE?')) return;
            try {
                const res = await fetch('/api/keys/' + id, { method: 'DELETE' });
                if (res.ok) {
                    loadKeys();
                    showToast('CLEARANCE TERMINATED');
                }
            } catch (e) {
                console.error("Failed to revoke key", e);
            }
        }

        function copyKey() {
            const input = document.getElementById('new_key_value');
            input.select();
            input.setSelectionRange(0, 99999);
            document.execCommand("copy");
            showToast('COPIED TO CLIPBOARD');
        }

        // Init
        loadOsInfo();
    </script>
</body>
</html>
"""
