import os

with open('desktop-app/web/script.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Add initVaultFileCreation and initVaultSearchAndView
vault_scripts = """

// --- Vault Explorer Additions ---
function initVaultFileCreation() {
    const btnCreateFolder = document.getElementById('btn-vault-create-folder');
    const inputFolder = document.getElementById('input-vault-new-folder');
    const btnCreateFile = document.getElementById('btn-vault-create-file');
    const inputFile = document.getElementById('input-vault-new-file');
    const btnRefresh = document.getElementById('btn-vault-refresh-dir');

    if(!btnCreateFolder) return;

    const handleCreateFolder = async () => {
        const folderName = inputFolder.value.trim();
        if (!folderName) return;
        try {
            const res = await callBackend('api_criar_pasta', vault_current_path, folderName);
            if (res.success) {
                logConsole(`[SUCESSO] Pasta criada no vault: ${folderName}`);
                inputFolder.value = '';
                render_vault_files(vault_current_path);
            } else {
                logConsole(`[ERRO] Falha ao criar pasta no vault: ${res.error}`);
            }
        } catch (e) {
            logConsole(`[ERRO FATAL] ${e.message}`);
        }
    };

    const handleCreateFile = async () => {
        const fileName = inputFile.value.trim();
        if (!fileName) return;
        try {
            const res = await callBackend('api_criar_ficheiro', vault_current_path, fileName);
            if (res.success) {
                logConsole(`[SUCESSO] Ficheiro criado no vault: ${fileName}`);
                inputFile.value = '';
                render_vault_files(vault_current_path);
            } else {
                logConsole(`[ERRO] Falha ao criar ficheiro no vault: ${res.error}`);
            }
        } catch (e) {
            logConsole(`[ERRO FATAL] ${e.message}`);
        }
    };

    btnCreateFolder.addEventListener('click', handleCreateFolder);
    btnCreateFile.addEventListener('click', handleCreateFile);
    inputFolder.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleCreateFolder(); });
    inputFile.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleCreateFile(); });

    btnRefresh.addEventListener('click', () => {
        if (vault_current_path) render_vault_files(vault_current_path);
    });
}

function initVaultSearchAndView() {
    const searchInput = document.getElementById('vault-search-input-box');
    const tableContainer = document.querySelector('#vault-explorer-container .files-table-container');
    const btnList = document.getElementById('btn-vault-view-list');
    const btnGrid = document.getElementById('btn-vault-view-grid');

    if(!searchInput) return;

    function applySearchFilter() {
        const term = searchInput.value.toLowerCase();
        const rows = document.querySelectorAll('#vault-files-body tr.file-row, #vault-files-body .grid-card');
        
        rows.forEach(row => {
            const nameEl = row.querySelector('.file-name');
            if (nameEl) {
                const name = nameEl.textContent.toLowerCase();
                row.style.display = name.includes(term) ? '' : 'none';
            }
        });
    }

    searchInput.addEventListener('input', applySearchFilter);

    if (btnList && btnGrid && tableContainer) {
        btnList.addEventListener('click', () => {
            btnGrid.classList.remove('active');
            btnList.classList.add('active');
            tableContainer.classList.remove('grid-mode');
            applySearchFilter();
        });

        btnGrid.addEventListener('click', () => {
            btnList.classList.remove('active');
            btnGrid.classList.add('active');
            tableContainer.classList.add('grid-mode');
            applySearchFilter();
        });
    }
}
"""

if "function initVaultFileCreation" not in text:
    text += vault_scripts

# Inject initialization calls inside startSystemCore
if "initVaultFileCreation()" not in text:
    text = text.replace("initVaultToggle();", "initVaultToggle();\n    initVaultFileCreation();\n    initVaultSearchAndView();")

with open('desktop-app/web/script.js', 'w', encoding='utf-8') as f:
    f.write(text)

print('done')
