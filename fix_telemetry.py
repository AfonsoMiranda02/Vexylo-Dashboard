import re

with open('desktop-app/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# I will just write a clean update_telemetry block

clean_func = """def update_telemetry(self):
    global last_api_post
    try:
        dados = get_telemetry_data()
        if dados:
            import json
            js_code = f"if (typeof update_telemetry_ui === 'function') update_telemetry_ui({json.dumps(dados)});"
            self.browser.page().runJavaScript(js_code)
            
            cpu_history.append(dados['cpu'])
            ram_history.append(dados['ram'])
            
            now = time.time()
            if now - last_api_post >= 300:
                if cpu_history and ram_history:
                    avg_cpu = sum(cpu_history) / len(cpu_history)
                    avg_ram = sum(ram_history) / len(ram_history)
                    payload = {"cpu_avg": avg_cpu, "ram_avg": avg_ram, "os_target": platform.system()}
                    try:
                        api_session.post(f"{API_BASE_URL}/api/system/logs", json=payload, timeout=3)
                    except Exception:
                        pass
                    cpu_history.clear()
                    ram_history.clear()
                    last_api_post = now
    except Exception as e:
        print(f"[!] Erro na telemetria: {e}")"""

# find the update_telemetry inside VexyloWindow
text = re.sub(r'def update_telemetry\(self\):.*?except Exception as e:\n\s*print\(f"\[!\] Erro no QTimer de telemetria: \{e\}"\)', clean_func, text, flags=re.DOTALL)

# remove the dangling update_telemetry definition that was placed outside by mistake
text = re.sub(r'def update_telemetry\(\):.*?time\.sleep\(1\.0\)', '', text, flags=re.DOTALL)

with open('desktop-app/main.py', 'w', encoding='utf-8') as f:
    f.write(text)
