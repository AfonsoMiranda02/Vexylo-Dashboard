import re

with open('desktop-app/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the indent of update_telemetry body
def indent_body(match):
    body = match.group(2)
    indented_body = "\n".join("        " + line if line.strip() else "" for line in body.split("\n"))
    return match.group(1) + indented_body

text = re.sub(r'(    def update_telemetry\(self\):\n)(    global last_api_post.*?print\(f"\[!\] Erro na telemetria: \{e\}"\))', indent_body, text, flags=re.DOTALL)

with open('desktop-app/main.py', 'w', encoding='utf-8') as f:
    f.write(text)
