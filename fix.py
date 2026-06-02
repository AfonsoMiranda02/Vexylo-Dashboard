import os

with open('desktop-app/web/script.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
for i, line in enumerate(lines):
    if line.startswith('async function render_files(path)'):
        start_idx = i
        break

if start_idx != -1:
    end_idx = start_idx
    depth = 0
    for i in range(start_idx, len(lines)):
        depth += lines[i].count('{') - lines[i].count('}')
        if depth == 0 and i > start_idx:
            end_idx = i
            break
            
    func_lines = lines[start_idx:end_idx+1]
    func_text = ''.join(func_lines)
    vault_func = func_text.replace('render_files', 'render_vault_files').replace('"files-list-body"', '"vault-files-body"').replace('"current-home-dir"', '"vault-current-dir"').replace('current_path', 'vault_current_path')
    
    with open('desktop-app/web/script.js', 'a', encoding='utf-8') as f:
        f.write('\nlet vault_current_path = null;\n')
        f.write(vault_func)
        f.write('\n')
    print('Done rendering vault')
else:
    print('Not found')
