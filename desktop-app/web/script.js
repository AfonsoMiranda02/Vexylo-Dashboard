/* ----------------------------------------------------
   NEXORA HUD COGNITIVE INTERFACE CONTROLLER (JS)
   ---------------------------------------------------- */


// --- QWebChannel Global Init ---
var backend = null;
const callBackend = (method, ...args) => new Promise(resolve => {
    if (!backend) {
        console.error("Backend offline.");
        resolve({success: false, error: "Backend offline"});
        return;
    }
    backend[method](...args, resolve);
});

document.addEventListener("DOMContentLoaded", () => {
    new QWebChannel(qt.webChannelTransport, function (channel) {
        backend = channel.objects.backend;
        console.log("QWebChannel Estabelecido.");
        
        // Ativar o lock screen da API Key
        initSystemAuth();
    });
});

function initSystemAuth() {
    const modal = document.getElementById("sys-api-key-modal");
    const input = document.getElementById("sys-api-key-input");
    const btn = document.getElementById("btn-unlock-system");
    const errorMsg = document.getElementById("sys-api-error");

    if(!modal) {
        startSystemCore();
        return;
    }

    input.focus();

    const tryAuth = async () => {
        const key = input.value;
        if(!key) return;
        
        btn.innerHTML = "[ VERIFYING... ]";
        const isValid = await callBackend('api_verificar_api_key', key);
        
        if (isValid) {
            modal.style.transition = "opacity 0.5s";
            modal.style.opacity = "0";
            setTimeout(() => {
                modal.style.display = "none";
                startSystemCore();
            }, 500);
        } else {
            errorMsg.style.display = "block";
            input.style.borderColor = "var(--neon-magenta)";
            btn.innerHTML = "[ AUTHENTICATE ]";
            input.value = "";
            setTimeout(() => {
                errorMsg.style.display = "none";
                input.style.borderColor = "var(--neon-cyan)";
            }, 2000);
        }
    };

    btn.addEventListener("click", tryAuth);
    input.addEventListener("keypress", (e) => {
        if(e.key === "Enter") tryAuth();
    });
}

function startSystemCore() {
    // Inicialização do sistema após Auth
    initClock();
    initTabs();
    initSystemDiagnostics();
    initApiStatusCheck();
    initFileManager();
    initFileCreation();
    initSearchAndView();
    initVaultToggle();
    initContextMenu();
    loadShortcuts();
    initNanoEditorShortcuts();
    initUnzipModal();
    initDeleteModal();
    initDatabaseManager();
    
    // Iniciar polling do Docker API
    checkApiStatus();
    setInterval(checkApiStatus, 5000);
    
    // Primeiro render
    eel_get_home_directory();
}

async function eel_get_home_directory() {
    let path = await callBackend('get_home_directory');
    if (path) render_files(path);
}

// Global State for Nexus
let isVaultMounted = false;
let context_menu_target_path = null;

// Helper: Log message to the HUD Sidebar Console
function logConsole(message) {
    const consoleLog = document.getElementById("sys-console-log");
    if (!consoleLog) return;

    const timestamp = new Date().toLocaleTimeString();
    const formattedMsg = `> [${timestamp}] ${message}<br>`;
    consoleLog.innerHTML += formattedMsg;

    // Auto-scroll to bottom
    consoleLog.scrollTop = consoleLog.scrollHeight;
}

// 1. SYSTEM CLOCK
function initClock() {
    const timeDisplay = document.getElementById("system-time");
    if (!timeDisplay) return;

    setInterval(() => {
        const now = new Date();
        timeDisplay.textContent = now.toLocaleTimeString();
    }, 1000);
}

// 2. TAB NAVIGATION (WITHOUT RELOADING)
function initTabs() {
    const tabButtons = document.querySelectorAll(".nav-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTabId = btn.getAttribute("data-tab");

            // Toggle active buttons
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            // Toggle active panes
            tabPanes.forEach(pane => {
                pane.classList.remove("active");
                if (pane.id === targetTabId) {
                    pane.classList.add("active");
                }
            });

            // Clean up iframe background consumption
            const apiPanel = document.getElementById("api-panel-container");
            const iframe = document.getElementById("api-iframe");
            const monitorGrid = document.querySelector(".monitor-grid");
            if (apiPanel && iframe && monitorGrid) {
                apiPanel.style.display = "none";
                monitorGrid.style.display = "grid";
                iframe.src = "";
            }

            logConsole(`Exibindo aba: ${btn.querySelector(".btn-text").textContent}`);

            // Action trigger when entering specific tabs
            if (targetTabId === "tab-files") {
                loadHomeFiles();
            } else if (targetTabId === "tab-database") {
                loadProfilesList();
            } else if (targetTabId === "tab-monitor") {
                checkApiStatus();
            }
        });
    });
}

// 3. SYSTEM OSTICS & OS SPECS
async function initSystemDiagnostics() {
    if (!backend) {
        logConsole("Aviso: Ambiente Eel não detetado (Mocking ativo).");
        return;
    }

    try {
        const info = await callBackend('obter_info_sistema');
        if (info && !info.error) {
            document.getElementById("spec-os").textContent = info.os_name || "Desconhecido";
            document.getElementById("spec-release").textContent = info.os_release || "-";
            document.getElementById("spec-arch").textContent = info.architecture || "-";
            document.getElementById("spec-cores").textContent = `${info.cpu_cores} Cores`;
            document.getElementById("spec-cpu").textContent = info.processor || "-";
            document.getElementById("spec-pyver").textContent = `v${info.python_version}` || "-";
            document.getElementById("spec-home").textContent = info.home_dir || "-";
            document.getElementById("spec-home").title = info.home_dir || "";
            logConsole("Módulos de hardware do SO mapeados com sucesso.");
        } else {
            logConsole(`Falha ao ler dados de OS: ${info.error}`);
        }
    } catch (e) {
        logConsole(`Erro ao invocar obter_info_sistema: ${e.message}`);
    }
}

// 4. API STATUS INTEGRATION
function initApiStatusCheck() {
    const recheckBtn = document.getElementById("btn-recheck-api");
    if (recheckBtn) {
        recheckBtn.addEventListener("click", () => {
            logConsole("Iniciando diagnóstico manual da API Docker...");
            checkApiStatus();
        });
    }

    const accessBtn = document.getElementById("btn-access-api");
    if (accessBtn) {
        accessBtn.addEventListener("click", () => {
            logConsole("A abrir Interface Swagger da API Docker...");
            document.getElementById("monitor-content-wrapper").style.display = "none";
            const iframeContainer = document.getElementById("api-iframe-container");
            iframeContainer.style.display = "flex";
            document.getElementById("api-iframe").src = "http://127.0.0.1:2060/";
        });
    }

    const closeIframeBtn = document.getElementById("btn-close-api-iframe");
    if (closeIframeBtn) {
        closeIframeBtn.addEventListener("click", () => {
            logConsole("A fechar Interface Swagger da API Docker...");
            document.getElementById("api-iframe-container").style.display = "none";
            document.getElementById("api-iframe").src = "";
            document.getElementById("monitor-content-wrapper").style.display = "grid";
        });
    }

    // Initial status check
    setTimeout(checkApiStatus, 500);
    // Auto polling every 10 seconds
    setInterval(checkApiStatus, 10000);
}

async function checkApiStatus() {
    const pulseDot = document.getElementById("pulse-indicator");
    const pulseText = document.getElementById("pulse-text");
    const statusBox = document.getElementById("api-status-box");
    const statusText = document.getElementById("api-status-text");
    const rawJsonDisplay = document.getElementById("api-response-raw");

    if (!backend) {
        return;
    }

    try {
        const status = await callBackend('obter_status_api');
        if (status.online) {
            // Update network pulse in header
            pulseDot.className = "pulse-dot online";
            pulseText.textContent = "API ONLINE";
            pulseText.style.color = "var(--neon-green)";

            // Update monitor status box
            statusBox.className = "status-indicator-box online";
            statusText.textContent = "ONLINE";

            // Format response json beautifully
            rawJsonDisplay.textContent = JSON.stringify(status.data, null, 4);
            rawJsonDisplay.style.color = "var(--neon-cyan)";

            logConsole("Diagnóstico de API concluído: Conexão Estável.");
        } else {
            // Update network pulse in header
            pulseDot.className = "pulse-dot offline";
            pulseText.textContent = "API OFFLINE";
            pulseText.style.color = "var(--neon-magenta)";

            // Update monitor status box
            statusBox.className = "status-indicator-box";
            statusText.textContent = "OFFLINE";

            // Format connection error details
            rawJsonDisplay.textContent = JSON.stringify({ "connection_error": status.error }, null, 4);
            rawJsonDisplay.style.color = "var(--neon-magenta)";

            logConsole(`Falha de conexão com a API: ${status.error}`);
        }
    } catch (e) {
        logConsole(`Excepção na chamada de diagnóstico API: ${e.message}`);
    }
}

// 5. FILE MANAGER INTEGRATION
let current_path = "";
let current_folder_images = [];
let current_image_index = 0;
let selected_item_path = null;
let selected_row_element = null;

async function initFileManager() {
    if (!backend) {
        logConsole("Aviso: Ambiente Eel não detetado para o Gestor de Ficheiros.");
        return;
    }

    // Preparar o botão BACK / UP LEVEL
    const pathBar = document.querySelector(".file-path-bar");
    if (pathBar && !document.getElementById("btn-up-level")) {
        pathBar.style.display = "flex";
        pathBar.style.alignItems = "center";

        const btnUp = document.createElement("button");
        btnUp.id = "btn-up-level";
        btnUp.className = "btn-secondary";
        btnUp.style.marginLeft = "auto";
        btnUp.textContent = "[ BACK // UP ONE LEVEL ]";

        btnUp.addEventListener("click", () => {
            if (current_path) {
                // Remover separadores finais
                const normalized = current_path.replace(/[\\/]+$/, '');
                const lastSlashIndex = Math.max(normalized.lastIndexOf('\\'), normalized.lastIndexOf('/'));

                if (lastSlashIndex > 0) { // Subir de nível, mantendo root slash / drive C:\ 
                    let newPath = normalized.substring(0, lastSlashIndex);
                    if (newPath.endsWith(':')) newPath += '\\'; // Edge caso Windows
                    render_files(newPath);
                } else if (lastSlashIndex === 0) { // Edge caso Linux root
                    render_files('/');
                }
            }
        });
        pathBar.appendChild(btnUp);
    }

    // Listener para o Enter na barra de navegação
    const pathInput = document.getElementById("current-home-dir");
    if (pathInput) {
        pathInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const newPath = pathInput.value.trim();
                if (newPath) {
                    render_files(newPath);
                }
            }
        });
    }

    // Inicializar os atalhos de teclado do Nano Editor
    initNanoEditorShortcuts();

    // Atalho F2 para Rename Global
    document.addEventListener("keydown", (e) => {
        if (e.key === "F2" && selected_item_path && selected_row_element) {
            e.preventDefault();
            if (selected_row_element.__itemData) {
                activateInlineRename(selected_row_element, selected_row_element.__itemData);
            }
        }
    });
}

let nano_current_file = "";

function initNanoEditorShortcuts() {
    // Bind Clicks
    const btnSave = document.getElementById("btn-nano-save");
    const btnExit = document.getElementById("btn-nano-exit");
    const btnCopy = document.getElementById("btn-nano-copy");
    const btnPaste = document.getElementById("btn-nano-paste");
    const btnFind = document.getElementById("btn-nano-find");
    
    if(btnSave) btnSave.addEventListener("click", nanoActionSave);
    if(btnExit) btnExit.addEventListener("click", nanoActionExit);
    if(btnCopy) btnCopy.addEventListener("click", nanoActionCopy);
    if(btnPaste) btnPaste.addEventListener("click", nanoActionPaste);
    if(btnFind) btnFind.addEventListener("click", nanoActionFind);

    // Find Input Logic
    const findInput = document.getElementById("nano-find-input");
    if(findInput) {
        findInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const query = findInput.value.toLowerCase();
                const textArea = document.getElementById("nano-textarea");
                if (query && textArea.value) {
                    let startPos = textArea.selectionEnd;
                    let text = textArea.value.toLowerCase();
                    let index = text.indexOf(query, startPos);
                    if (index === -1) index = text.indexOf(query, 0); // Wrap around
                    
                    if (index !== -1) {
                        textArea.focus();
                        textArea.setSelectionRange(index, index + query.length);
                    } else {
                        const statusSpan = document.getElementById("nano-status");
                        statusSpan.textContent = "NOT FOUND";
                        setTimeout(() => { if (statusSpan.textContent === "NOT FOUND") statusSpan.textContent = ""; }, 2000);
                    }
                }
            } else if (e.key === "Escape") {
                document.getElementById("nano-find-container").style.display = "none";
                document.getElementById("nano-textarea").focus();
            }
        });
    }

    // Bind Keyboard Shortcuts
    document.addEventListener("keydown", async (e) => {
        const nanoOverlay = document.getElementById("nano-overlay");
        const isNanoOpen = nanoOverlay && nanoOverlay.style.display === "flex";

        if (isNanoOpen && e.ctrlKey) {
            const key = e.key.toLowerCase();
            if (key === 's') { e.preventDefault(); nanoActionSave(); }
            if (key === 'x') { e.preventDefault(); nanoActionExit(); }
            if (key === 'c') { e.preventDefault(); nanoActionCopy(); }
            if (key === 'v') { e.preventDefault(); nanoActionPaste(); }
            if (key === 'f') { e.preventDefault(); nanoActionFind(); }
        }
    });
}

async function nanoActionSave() {
    const textArea = document.getElementById("nano-textarea");
    const statusSpan = document.getElementById("nano-status");

    statusSpan.textContent = "Saving...";
    try {
        const res = await callBackend('save_file_content', nano_current_file, textArea.value);
        if (res.success) {
            statusSpan.textContent = "FILE SAVED";
            logConsole(`Ficheiro guardado com sucesso: ${nano_current_file}`);
        } else {
            statusSpan.textContent = `ERROR: ${res.error}`;
            logConsole(`Erro ao guardar ficheiro: ${res.error}`);
        }
    } catch (err) {
        statusSpan.textContent = `FAILED`;
        logConsole(`Falha na API de gravação: ${err.message}`);
    }

    setTimeout(() => { if (statusSpan.textContent === "FILE SAVED") statusSpan.textContent = ""; }, 2000);
}

function nanoActionExit() {
    document.getElementById("nano-overlay").style.display = "none";
    document.getElementById("files-table-container").style.display = "block";
    document.getElementById("nano-textarea").value = "";
    document.getElementById("nano-find-container").style.display = "none";
    nano_current_file = "";
    render_files(current_path);
}

function nanoActionCopy() {
    const textArea = document.getElementById("nano-textarea");
    const text = textArea.value.substring(textArea.selectionStart, textArea.selectionEnd);
    if (text) {
        navigator.clipboard.writeText(text);
        const statusSpan = document.getElementById("nano-status");
        statusSpan.textContent = "COPIED";
        setTimeout(() => { if (statusSpan.textContent === "COPIED") statusSpan.textContent = ""; }, 2000);
    }
}

async function nanoActionPaste() {
    try {
        const text = await navigator.clipboard.readText();
        if (text) {
            const textArea = document.getElementById("nano-textarea");
            const start = textArea.selectionStart;
            const end = textArea.selectionEnd;
            const val = textArea.value;
            textArea.value = val.substring(0, start) + text + val.substring(end);
            textArea.selectionStart = textArea.selectionEnd = start + text.length;
            textArea.focus();
            
            const statusSpan = document.getElementById("nano-status");
            statusSpan.textContent = "PASTED";
            setTimeout(() => { if (statusSpan.textContent === "PASTED") statusSpan.textContent = ""; }, 2000);
        }
    } catch (e) {
        logConsole(`Acesso ao clipboard negado: ${e.message}`);
    }
}

function nanoActionFind() {
    const findContainer = document.getElementById("nano-find-container");
    const findInput = document.getElementById("nano-find-input");
    findContainer.style.display = "block";
    findInput.focus();
}

async function openNanoEditor(filePath) {
    logConsole(`Abrindo no Nano: ${filePath}`);
    const textArea = document.getElementById("nano-textarea");
    const statusSpan = document.getElementById("nano-status");

    document.getElementById("files-table-container").style.display = "none";
    document.getElementById("nano-overlay").style.display = "flex";

    statusSpan.textContent = `Reading ${filePath}...`;
    nano_current_file = filePath;
    textArea.value = "Carregando conteúdo...";

    try {
        const res = await callBackend('read_file_content', filePath);
        if (res.success) {
            textArea.value = res.content;
            statusSpan.textContent = "";
        } else {
            textArea.value = `ERROR LENDO FICHEIRO: ${res.error}`;
            statusSpan.textContent = "READ ERROR";
        }
    } catch (e) {
        textArea.value = `FALHA FATAL: ${e.message}`;
        statusSpan.textContent = "FATAL ERROR";
    }
}

async function loadHomeFiles() {
    if (!current_path && backend) {
        try {
            current_path = await callBackend('get_home_directory');
        } catch (e) {
            logConsole(`Erro ao obter home: ${e}`);
        }
    }
    if (current_path) {
        render_files(current_path);
    }
}

async function render_files(path) {
    const body = document.getElementById("files-list-body");
    const pathVal = document.getElementById("current-home-dir");

    if (!body) return;
    body.innerHTML = `<tr><td colspan="4" class="loading-td">A varrer o diretório: ${path}...</td></tr>`;

    if (!backend) {
        body.innerHTML = `<tr><td colspan="4" class="loading-td" style="color:var(--neon-magenta)">Erro: Ambiente Eel indisponível.</td></tr>`;
        return;
    }

    try {
        const res = await callBackend('list_directory_contents', path, false);
        if (res.success) {
            current_path = res.path;
            pathVal.value = current_path; // Atualizar o input ao invés de span

            if (res.items.length === 0) {
                body.innerHTML = `<tr><td colspan="4" class="loading-td">Pasta vazia ou sem acessibilidade.</td></tr>`;
                return;
            }

            body.innerHTML = "";
            current_folder_images = [];
            
            res.items.forEach(item => {
                const extLower = item.extension ? item.extension.toLowerCase() : "";
                const imageExts = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico"];
                if (!item.is_dir && imageExts.includes(extLower)) {
                    current_folder_images.push(item);
                }
                
                const tr = document.createElement("tr");

                // Icon e tipo
                const icon = item.is_dir ? "📁" : "📄";
                const iconClass = item.is_dir ? "icon-pasta" : "icon-ficheiro";
                const tipoDisplay = item.is_dir ? "Pasta" : `Ficheiro ${item.extension}`;

                let utilsHtml = '';
                const safePath = item.path.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
                const isZip = item.extension && item.extension.toLowerCase() === '.zip';

                if (item.is_dir) {
                    utilsHtml = `
                        <button class="btn-micro cyan" onclick="event.stopPropagation(); scanFolderSize(this, '${safePath}')">[ SCAN ]</button>
                        <button class="btn-micro green" onclick="event.stopPropagation(); createZipFile('${safePath}')">[ ZIP ]</button>
                        <button class="btn-micro orange" onclick="event.stopPropagation(); activateInlineRename(this.closest('tr'), this.closest('tr').__itemData)">[ REN ]</button>
                        <button class="btn-micro magenta" onclick="event.stopPropagation(); deleteItem('${safePath}')">[ DEL ]</button>
                    `;
                } else if (item.extension && item.extension.toLowerCase() === '.batlock') {
                    utilsHtml = `
                        <button class="btn-micro yellow" onclick="event.stopPropagation(); logConsole('Editar desabilitado para arquivos batlock: ${safePath}')" disabled>[ EDIT ]</button>
                        <button class="btn-micro cyan" onclick="event.stopPropagation(); decryptItem('${safePath}')">[ DEC ]</button>
                        <button class="btn-micro orange" onclick="event.stopPropagation(); activateInlineRename(this.closest('tr'), this.closest('tr').__itemData)">[ REN ]</button>
                        <button class="btn-micro magenta" onclick="event.stopPropagation(); deleteItem('${safePath}')">[ DEL ]</button>
                    `;
                } else if (isZip) {
                    utilsHtml = `
                        <button class="btn-micro yellow" onclick="event.stopPropagation(); openNanoEditor('${safePath}')">[ EDIT ]</button>
                        <button class="btn-micro green" onclick="event.stopPropagation(); extractZipFile('${safePath}')">[ UNZ ]</button>
                        <button class="btn-micro cyan" onclick="event.stopPropagation(); ${isVaultMounted && current_path === 'VAULT://' ? `extractFromVault('${safePath}')` : `encryptItem('${safePath}')`}">${isVaultMounted && current_path === 'VAULT://' ? '[ EXTR ]' : '[ ENC ]'}</button>
                        <button class="btn-micro orange" onclick="event.stopPropagation(); activateInlineRename(this.closest('tr'), this.closest('tr').__itemData)">[ REN ]</button>
                        <button class="btn-micro magenta" onclick="event.stopPropagation(); ${isVaultMounted && current_path === 'VAULT://' ? `deleteFromVault('${item.name}')` : `deleteItem('${safePath}')`} ">[ DEL ]</button>
                    `;
                } else {
                    utilsHtml = `
                        <button class="btn-micro yellow" onclick="event.stopPropagation(); openNanoEditor('${safePath}')">[ EDIT ]</button>
                        <button class="btn-micro green" onclick="event.stopPropagation(); createZipFile('${safePath}')">[ ZIP ]</button>
                        <button class="btn-micro cyan" onclick="event.stopPropagation(); ${isVaultMounted && current_path === 'VAULT://' ? `extractFromVault('${safePath}')` : `encryptItem('${safePath}')`}">${isVaultMounted && current_path === 'VAULT://' ? '[ EXTR ]' : '[ ENC ]'}</button>
                        <button class="btn-micro orange" onclick="event.stopPropagation(); activateInlineRename(this.closest('tr'), this.closest('tr').__itemData)">[ REN ]</button>
                        <button class="btn-micro magenta" onclick="event.stopPropagation(); ${isVaultMounted && current_path === 'VAULT://' ? `deleteFromVault('${item.name}')` : `deleteItem('${safePath}')`} ">[ DEL ]</button>
                    `;
                }

                tr.innerHTML = `
                    <td class="type-cell ${item.is_dir ? 'neon-yellow' : ''}"><span class="icon ${iconClass}">${icon}</span> <span>${tipoDisplay}</span></td>
                    <td class="file-name-cell name-cell" style="font-weight: ${item.is_dir ? 'bold' : 'normal'}">${item.name}</td>
                    <td class="align-right size-cell">${item.size}</td>
                    <td class="align-right utils-cell">${utilsHtml}</td>
                `;

                // Anexar dados do item ao TR para acesso no F2 e afins
                tr.__itemData = item;
                tr.style.cursor = "pointer";
                tr.title = item.is_dir ? "Duplo clique para abrir a pasta" : "Duplo clique para abrir ficheiro";

                // Listener de cliques dinâmicos usando e.detail
                tr.addEventListener("click", (e) => {
                    // Ignorar cliques nos botões utilitários ou dentro de inputs
                    if (e.target.closest('.btn-micro') || e.target.closest('input')) return;

                    // [ 1 Clique ]: Seleção Tática
                    if (selected_row_element && selected_row_element !== tr) {
                        selected_row_element.classList.remove('selected-row');
                    }
                    tr.classList.add('selected-row');
                    selected_row_element = tr;
                    selected_item_path = item.path;

                    // Fechar menu de contexto se aberto no click esquerdo
                    const ctxMenu = document.getElementById("custom-context-menu");
                    if(ctxMenu) ctxMenu.style.display = "none";

                    if (e.detail === 2) {
                        // [ 2 Cliques ]: Abrir/Entrar
                        if (item.is_dir || (item.extension && item.extension.toLowerCase() === '.zip')) {
                            render_files(item.path);
                        } else {
                            const validExts = [".txt", ".log", ".json", ".py", ".md", ".ini", ".js", ".html", ".css", ".csv"];
                            const imageExts = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico"];
                            const extLower = item.extension ? item.extension.toLowerCase() : "";
                            
                            if (validExts.includes(extLower) || !extLower) {
                                openNanoEditor(item.path);
                            } else if (imageExts.includes(extLower)) {
                                logConsole(`Abrindo imagem no visualizador interno: ${item.name}`);
                                const idx = current_folder_images.findIndex(img => img.path === item.path);
                                if (idx !== -1) {
                                    current_image_index = idx;
                                    updateImageViewer();
                                    const modal = document.getElementById("image-viewer-modal");
                                    if (modal) modal.style.display = "flex";
                                }
                            } else {
                                logConsole(`Sem suporte nativo para ler ficheiros ${item.extension}.`);
                            }
                        }
                    } else if (e.detail === 3) {
                        // [ 3 Cliques ]: Inline Rename Instântaneo
                        activateInlineRename(tr, item);
                    }
                });


                // Feedback visual hover
                tr.title = item.is_dir ? "Duplo clique para abrir a pasta" : "Duplo clique para abrir ficheiro (se texto)";
                tr.addEventListener("mouseenter", () => tr.style.background = "rgba(0, 255, 255, 0.1)");
                tr.addEventListener("mouseleave", () => tr.style.background = "");

                // Interceptar Context Menu
                tr.addEventListener('contextmenu', (e) => {
                    e.preventDefault();
                    context_menu_target_path = item.path;
                    selected_row_element = tr;
                    selected_item_path = item.path;
                    
                    const menu = document.getElementById("custom-context-menu");
                    if(menu) {
                        menu.style.display = "block";
                        menu.style.left = e.pageX + "px";
                        menu.style.top = e.pageY + "px";
                    }
                });

                body.appendChild(tr);
            });

            logConsole(`Diretório acedido com sucesso.`);
        } else {
            body.innerHTML = `<tr><td colspan="4" class="loading-td" style="color:var(--neon-magenta)">Erro: ${res.error}</td></tr>`;
            logConsole(`Erro ao listar pasta: ${res.error}`);
        }
    } catch (e) {
        body.innerHTML = `<tr><td colspan="4" class="loading-td" style="color:var(--neon-magenta)">Falha: ${e.message}</td></tr>`;
        logConsole(`Falha do motor de ficheiros: ${e.message}`);
    }
}

let current_unzip_target = "";

function initUnzipModal() {
    const unzipModal = document.getElementById('unzip-modal');
    const unzipExecute = document.getElementById('unzip-btn-execute');
    const unzipAbort = document.getElementById('unzip-btn-abort');
    
    if (unzipExecute) {
        unzipExecute.addEventListener('click', async () => {
            const destInput = document.getElementById('unzip-dest-input').value.trim();
            const criarSubpasta = document.getElementById('unzip-opt-subfolder').checked;
            
            unzipModal.style.display = 'none';
            logConsole(`A executar protocolo de extração para: ${current_unzip_target}`);
            
            try {
                const res = await callBackend('api_extrair_zip_avancado', current_unzip_target, destInput, criarSubpasta);
                if (res.success) {
                    logConsole(`[SUCESSO] ZIP extraído para: ${res.extracted_to}`);
                    render_files(current_path);
                } else {
                    logConsole(`[ERRO] Falha ao extrair ZIP: ${res.error}`);
                }
            } catch (e) {
                logConsole(`[ERRO FATAL] Falha na comunicação com Python: ${e.message}`);
            }
        });
    }
    
    if (unzipAbort) {
        unzipAbort.addEventListener('click', () => {
            unzipModal.style.display = 'none';
            logConsole("Extração cancelada pelo utilizador.");
        });
    }
}

function extractZipFile(zipPath) {
    current_unzip_target = zipPath;
    const modal = document.getElementById('unzip-modal');
    const destInput = document.getElementById('unzip-dest-input');
    
    destInput.value = current_path;
    modal.style.display = 'flex';
}

async function createZipFile(path) {
    logConsole(`A comprimir para ZIP: ${path}`);
    try {
        const res = await callBackend('api_criar_zip', path);
        if (res.success) {
            logConsole(`[SUCESSO] ZIP criado: ${res.zip_path}`);
            render_files(current_path);
        } else {
            logConsole(`[ERRO] Falha ao criar ZIP: ${res.error}`);
        }
    } catch (e) {
        logConsole(`[ERRO FATAL] Motor de compressão falhou: ${e.message}`);
    }
}

function activateInlineRename(tr, item) {
    const nameCell = tr.querySelector('.file-name-cell');
    if (!nameCell || nameCell.querySelector('input')) return;

    const currentName = item.name;
    const input = document.createElement("input");
    input.type = "text";
    input.value = currentName;
    input.className = "inline-rename-input";
    input.style.width = "100%";
    input.style.background = "rgba(0, 0, 0, 0.8)";
    input.style.border = "1px solid var(--neon-cyan)";
    input.style.color = "var(--neon-yellow)";
    input.style.fontFamily = "var(--font-mono)";
    input.style.fontSize = "inherit";
    input.style.padding = "2px 5px";
    input.style.outline = "none";

    const handleRename = async () => {
        const newName = input.value.trim();
        if (newName && newName !== currentName) {
            try {
                const res = await callBackend('api_renomear_item', item.path, newName);
                if (res.success) {
                    logConsole(`Item renomeado para: ${newName}`);
                    // Atualizar estado global caso a alteração mude o path
                    if (selected_item_path === item.path) {
                        selected_item_path = null;
                        selected_row_element = null;
                    }
                    render_files(current_path);
                } else {
                    logConsole(`Erro ao renomear: ${res.error}`);
                    nameCell.textContent = currentName;
                }
            } catch (err) {
                logConsole(`Falha na API de renomear: ${err.message}`);
                nameCell.textContent = currentName;
            }
        } else {
            nameCell.textContent = currentName;
        }
    };

    input.addEventListener("blur", handleRename);
    input.addEventListener("keydown", (evt) => {
        if (evt.key === "Enter") {
            input.blur();
        } else if (evt.key === "Escape") {
            input.removeEventListener("blur", handleRename);
            nameCell.textContent = currentName;
        }
    });

    nameCell.innerHTML = "";
    nameCell.appendChild(input);
    input.focus();

    if (!item.is_dir && item.name.includes('.')) {
        const lastDotIndex = item.name.lastIndexOf('.');
        if (lastDotIndex > 0) input.setSelectionRange(0, lastDotIndex);
        else input.select();
    } else {
        input.select();
    }
}

async function scanFolderSize(btn, path) {
    btn.textContent = "[ SCANNING... ]";
    btn.disabled = true;
    try {
        const sizeStr = await callBackend('api_calcular_tamanho_pasta', path);
        const tr = btn.closest('tr');
        if (tr) {
            const sizeCell = tr.querySelector('.size-cell');
            if (sizeCell) sizeCell.textContent = sizeStr;
        }
        btn.textContent = "[ SCAN SIZE ]";
        btn.disabled = false;
    } catch (e) {
        btn.textContent = "[ ERROR ]";
        logConsole(`Erro ao calcular tamanho da pasta: ${e.message}`);
        btn.disabled = false;
    }
}

let current_delete_target = "";

function initDeleteModal() {
    const deleteModal = document.getElementById('delete-modal');
    const deleteExecute = document.getElementById('delete-btn-execute');
    const deleteAbort = document.getElementById('delete-btn-abort');
    
    if (deleteExecute) {
        deleteExecute.addEventListener('click', async () => {
            deleteModal.style.display = 'none';
            try {
                const res = await callBackend('execute_file_system_action', 'delete', current_delete_target, "");
                if (res && res.success) {
                    logConsole(`[SUCESSO] Item eliminado: ${current_delete_target}`);
                    render_files(current_path);
                } else {
                    logConsole(`[ERRO] Falha ao eliminar: ${res.error}`);
                }
            } catch (e) {
                logConsole(`[ERRO FATAL] Motor de eliminação falhou: ${e.message}`);
            }
        });
    }
    
    if (deleteAbort) {
        deleteAbort.addEventListener('click', () => {
            deleteModal.style.display = 'none';
            logConsole("Eliminação abortada pelo utilizador.");
        });
    }

    // IMAGE VIEWER MODAL LOGIC
    const imgModalCloseBtn = document.getElementById('btn-close-image-viewer');
    if (imgModalCloseBtn) {
        imgModalCloseBtn.addEventListener('click', () => {
            const modal = document.getElementById("image-viewer-modal");
            const img = document.getElementById("image-viewer-img");
            if (modal) modal.style.display = "none";
            if (img) img.src = ""; // Stop loading or free memory
        });
    }

    const btnPrevImg = document.getElementById('btn-prev-image');
    const btnNextImg = document.getElementById('btn-next-image');
    
    // ZOOM SLIDER LOGIC
    const zoomSlider = document.getElementById('image-viewer-zoom');
    const zoomVal = document.getElementById('image-viewer-zoom-val');
    
    if (zoomVal) {
        zoomVal.addEventListener('change', (e) => {
            let val = parseInt(e.target.value);
            if (isNaN(val)) val = 100;
            if (zoomSlider) {
                zoomSlider.value = Math.min(Math.max(val, parseInt(zoomSlider.min)), parseInt(zoomSlider.max));
                zoomSlider.dispatchEvent(new Event('input'));
            }
        });
    }

    if (zoomSlider) {
        zoomSlider.addEventListener('input', (e) => {
            const zoom = e.target.value;
            if (zoomVal) zoomVal.value = zoom;
            const img = document.getElementById('image-viewer-img');
            if (img && img.dataset.baseWidth && img.dataset.baseHeight) {
                img.style.maxWidth = 'none';
                img.style.maxHeight = 'none';
                img.style.flexShrink = '0';
                
                const factor = zoom / 100;
                img.style.width = (parseFloat(img.dataset.baseWidth) * factor) + 'px';
                img.style.height = (parseFloat(img.dataset.baseHeight) * factor) + 'px';
            }
        });
    }

    // PAN AND WHEEL ZOOM LOGIC
    const imgContainer = document.getElementById('image-viewer-container');
    let isDraggingImg = false;
    let startX = 0;
    let startY = 0;
    let scrollLeftStart = 0;
    let scrollTopStart = 0;

    if (imgContainer) {
        imgContainer.addEventListener('mousedown', (e) => {
            if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'INPUT') {
                isDraggingImg = true;
                startX = e.pageX;
                startY = e.pageY;
                scrollLeftStart = imgContainer.scrollLeft;
                scrollTopStart = imgContainer.scrollTop;
                imgContainer.style.cursor = 'grabbing';
                e.preventDefault(); // prevent default image drag
            }
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDraggingImg) return;
            const x = e.pageX - startX;
            const y = e.pageY - startY;
            imgContainer.scrollLeft = scrollLeftStart - x;
            imgContainer.scrollTop = scrollTopStart - y;
        });

        document.addEventListener('mouseup', () => {
            isDraggingImg = false;
            if (imgContainer) imgContainer.style.cursor = 'default';
        });

        imgContainer.addEventListener('wheel', (e) => {
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'INPUT') return;
            e.preventDefault();
            if (zoomSlider) {
                const img = document.getElementById('image-viewer-img');
                let rect = img.getBoundingClientRect();
                let mouseX = e.clientX - rect.left;
                let mouseY = e.clientY - rect.top;
                
                let ratioX = mouseX / img.clientWidth;
                let ratioY = mouseY / img.clientHeight;

                let currentZoom = parseInt(zoomSlider.value);
                let zoomDelta = e.deltaY < 0 ? 25 : -25;
                let newZoom = Math.min(Math.max(currentZoom + zoomDelta, parseInt(zoomSlider.min)), parseInt(zoomSlider.max));
                zoomSlider.value = newZoom;
                
                zoomSlider.dispatchEvent(new Event('input'));
                
                let newMouseX = img.clientWidth * ratioX;
                let newMouseY = img.clientHeight * ratioY;
                
                imgContainer.scrollLeft += newMouseX - mouseX;
                imgContainer.scrollTop += newMouseY - mouseY;
            }
        }, { passive: false });
    }

    if (btnPrevImg) {
        btnPrevImg.addEventListener('click', () => {
            if (current_image_index > 0) {
                current_image_index--;
                updateImageViewer();
            }
        });
    }
    
    if (btnNextImg) {
        btnNextImg.addEventListener('click', () => {
            if (current_image_index < current_folder_images.length - 1) {
                current_image_index++;
                updateImageViewer();
            }
        });
    }

    document.addEventListener('keydown', (e) => {
        if (deleteModal && deleteModal.style.display === 'flex') {
            if (e.key === 'Escape') {
                deleteModal.style.display = 'none';
                logConsole("Eliminação abortada pelo utilizador.");
            } else if (e.key === 'Enter') {
                deleteExecute.click();
            }
        }
        
        const imgModal = document.getElementById("image-viewer-modal");
        if (imgModal && imgModal.style.display === 'flex') {
            if (e.key === 'Escape') {
                const btnClose = document.getElementById('btn-close-image-viewer');
                if (btnClose) btnClose.click();
            } else if (e.key === 'ArrowLeft') {
                const btnPrev = document.getElementById('btn-prev-image');
                if (btnPrev && btnPrev.style.display !== 'none') btnPrev.click();
            } else if (e.key === 'ArrowRight') {
                const btnNext = document.getElementById('btn-next-image');
                if (btnNext && btnNext.style.display !== 'none') btnNext.click();
            }
        }
    });
}

function deleteItem(path) {
    current_delete_target = path;
    const modal = document.getElementById('delete-modal');
    const pathDisplay = document.getElementById('delete-modal-path');
    
    pathDisplay.textContent = path;
    modal.style.display = 'flex';
}

function initFileCreation() {
    const btnCreateFolder = document.getElementById('btn-create-folder');
    const inputFolder = document.getElementById('input-new-folder');
    const btnCreateFile = document.getElementById('btn-create-file');
    const inputFile = document.getElementById('input-new-file');
    const btnRefresh = document.getElementById('btn-refresh-dir');

    const handleCreateFolder = async () => {
        const folderName = inputFolder.value.trim();
        if (!folderName) return;
        try {
            const res = await callBackend('api_criar_pasta', current_path, folderName);
            if (res.success) {
                logConsole(`[SUCESSO] Pasta criada: ${folderName}`);
                inputFolder.value = '';
                render_files(current_path);
            } else {
                logConsole(`[ERRO] Falha ao criar pasta: ${res.error}`);
            }
        } catch (e) {
            logConsole(`[ERRO FATAL] ${e.message}`);
        }
    };

    const handleCreateFile = async () => {
        const fileName = inputFile.value.trim();
        if (!fileName) return;
        try {
            const res = await callBackend('api_criar_ficheiro', current_path, fileName);
            if (res.success) {
                logConsole(`[SUCESSO] Ficheiro criado: ${fileName}`);
                inputFile.value = '';
                render_files(current_path);
                openNanoEditor(res.full_path);
            } else {
                logConsole(`[ERRO] Falha ao criar ficheiro: ${res.error}`);
            }
        } catch (e) {
            logConsole(`[ERRO FATAL] ${e.message}`);
        }
    };

    if (btnCreateFolder) btnCreateFolder.addEventListener('click', handleCreateFolder);
    if (inputFolder) inputFolder.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleCreateFolder(); });

    if (btnCreateFile) btnCreateFile.addEventListener('click', handleCreateFile);
    if (inputFile) inputFile.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleCreateFile(); });

    if (btnRefresh) btnRefresh.addEventListener('click', () => {
        if (current_path) render_files(current_path);
    });
}

function initSearchAndView() {
    const searchInput = document.getElementById('search-input-box');
    const btnList = document.getElementById('btn-view-list');
    const btnGrid = document.getElementById('btn-view-grid');
    const tableContainer = document.getElementById('files-table-container');

    const applySearchFilter = () => {
        if (!searchInput) return;
        const searchTerm = searchInput.value.toLowerCase().trim();
        const fileRows = document.querySelectorAll('#files-list-body tr');
        
        fileRows.forEach(row => {
            if (row.querySelector('.loading-td')) return;
            
            const nameElement = row.querySelector('.name-cell');
            
            if (nameElement) {
                const fileName = nameElement.textContent.toLowerCase();
                const isEditing = nameElement.querySelector('input');
                
                if (fileName.includes(searchTerm) || isEditing) {
                    if (tableContainer.classList.contains('grid-mode')) {
                        row.style.setProperty('display', 'flex', 'important');
                    } else {
                        row.style.setProperty('display', 'table-row', 'important');
                    }
                } else {
                    row.style.setProperty('display', 'none', 'important');
                }
            }
        });
    };

    if (searchInput) {
        searchInput.addEventListener('input', applySearchFilter);
    }

    if (btnList && btnGrid && tableContainer) {
        btnList.addEventListener('click', () => {
            btnList.classList.add('active');
            btnGrid.classList.remove('active');
            tableContainer.classList.remove('grid-mode');
            applySearchFilter();
        });
        
        btnGrid.addEventListener('click', () => {
            btnGrid.classList.add('active');
            btnList.classList.remove('active');
            tableContainer.classList.add('grid-mode');
            applySearchFilter();
        });
    }
}

// --- Nexus Phase 1 & 2 Logic ---
function initVaultToggle() {
    const btn = document.getElementById("btn-toggle-vault");
    const modal = document.getElementById("vault-auth-modal");
    const pwdInput = document.getElementById("vault-password");
    
    if(!btn || !modal) return;
    
    btn.addEventListener("click", async () => {
        if(isVaultMounted) {
            // Unmount
            const res = await callBackend('api_unmount_vault');
            logConsole(res.msg || res.error);
            isVaultMounted = false;
            btn.style.color = "rgba(255, 255, 255, 0.4)";
            btn.style.textShadow = "none";
            render_files(await callBackend('get_home_directory'));
        } else {
            // Open Mount Modal
            modal.style.display = "flex";
            pwdInput.value = "";
            pwdInput.focus();
        }
    });

    document.getElementById("btn-vault-cancel").addEventListener("click", () => {
        modal.style.display = "none";
    });

    document.getElementById("btn-vault-mount").addEventListener("click", async () => {
        const pwd = pwdInput.value;
        if(!pwd) return;
        
        const res = await callBackend('api_mount_vault', pwd);
        if(res.success) {
            logConsole(res.msg);
            isVaultMounted = true;
            btn.style.color = "var(--neon-green)";
            btn.style.textShadow = "0 0 10px var(--neon-green)";
            modal.style.display = "none";
            render_files("VAULT://");
        } else {
            logConsole(`Vault Error: ${res.error}`);
            pwdInput.style.borderColor = "var(--neon-magenta)";
            setTimeout(() => pwdInput.style.borderColor = "var(--neon-cyan)", 1000);
        }
    });
}

async function extractFromVault(filePath) {
    const targetDir = await callBackend('get_home_directory'); // ou um prompt
    const filename = filePath.split('//')[1];
    const res = await callBackend('api_extract_from_vault', filename, targetDir);
    logConsole(res.msg || res.error);
    render_files("VAULT://");
}

async function deleteFromVault(filename) {
    if(confirm(`Permanentemente eliminar ${filename} do cofre?`)) {
        const res = await callBackend('api_delete_from_vault', filename);
        logConsole(res.msg || res.error);
        render_files("VAULT://");
    }
}

function initContextMenu() {
    const menu = document.getElementById("custom-context-menu");
    if(!menu) return;

    document.addEventListener("click", (e) => {
        if(!e.target.closest('#custom-context-menu')) {
            menu.style.display = "none";
        }
    });

    document.getElementById("ctx-pin").addEventListener("click", async () => {
        if(!context_menu_target_path) return;
        const res = await callBackend('api_toggle_pin', context_menu_target_path);
        logConsole(res.msg);
        loadShortcuts();
        menu.style.display = "none";
    });

    document.getElementById("ctx-fav").addEventListener("click", async () => {
        if(!context_menu_target_path) return;
        const res = await callBackend('api_toggle_favorite', context_menu_target_path);
        logConsole(res.msg);
        loadShortcuts();
        menu.style.display = "none";
    });

    document.getElementById("ctx-vault").addEventListener("click", async () => {
        if(!context_menu_target_path) return;
        if(!isVaultMounted) {
            logConsole("Cofre bloqueado. Montar primeiro.");
            menu.style.display = "none";
            return;
        }
        const res = await callBackend('api_move_to_vault', context_menu_target_path);
        logConsole(res.msg || res.error);
        if(current_path) render_files(current_path);
        menu.style.display = "none";
    });

    document.getElementById("ctx-ren").addEventListener("click", () => {
        if(!context_menu_target_path || !selected_row_element || !selected_row_element.__itemData) return;
        activateInlineRename(selected_row_element, selected_row_element.__itemData);
        menu.style.display = "none";
    });

    document.getElementById("ctx-del").addEventListener("click", () => {
        if(!context_menu_target_path) return;
        deleteItem(context_menu_target_path);
        menu.style.display = "none";
    });
}

async function loadShortcuts() {
    const container = document.getElementById("sidebar-shortcuts-container");
    if(!container) return;
    
    if(!backend) return;
    
    try {
        const res = await callBackend('api_get_user_shortcuts');
        if(res.success) {
            container.innerHTML = "";
            
            if(res.pins.length === 0 && res.favs.length === 0) {
                container.innerHTML = `<span style="color: rgba(255,255,255,0.4); font-size: 10px;">> Sem atalhos ou favoritos.</span>`;
                return;
            }

            res.favs.forEach(p => {
                const btn = document.createElement("div");
                btn.className = "shortcut-link";
                btn.innerHTML = `⭐ ${p.split(/[\\/]/).pop() || p}`;
                btn.title = p;
                btn.onclick = () => render_files(p);
                container.appendChild(btn);
            });

            res.pins.forEach(p => {
                const btn = document.createElement("div");
                btn.className = "shortcut-link";
                btn.innerHTML = `📌 ${p.split(/[\\/]/).pop() || p}`;
                btn.title = p;
                btn.onclick = () => render_files(p);
                container.appendChild(btn);
            });
        }
    } catch (e) {
        console.error(e);
    }
}

function promptCryptoPassword() {
    return new Promise((resolve) => {
        const modal = document.getElementById('crypto-modal');
        const input = document.getElementById('crypto-input');
        const btnConfirm = document.getElementById('crypto-btn-confirm');
        const btnCancel = document.getElementById('crypto-btn-cancel');

        modal.style.display = 'flex';
        input.value = '';
        input.focus();

        const cleanup = () => {
            modal.style.display = 'none';
            btnConfirm.removeEventListener('click', onConfirm);
            btnCancel.removeEventListener('click', onCancel);
            input.removeEventListener('keydown', onKeydown);
        };

        const onConfirm = () => {
            cleanup();
            resolve(input.value.trim());
        };

        const onCancel = () => {
            cleanup();
            resolve(null);
        };

        const onKeydown = (e) => {
            if (e.key === 'Enter') onConfirm();
            if (e.key === 'Escape') onCancel();
        };

        btnConfirm.addEventListener('click', onConfirm);
        btnCancel.addEventListener('click', onCancel);
        input.addEventListener('keydown', onKeydown);
    });
}

async function encryptItem(path) {
    let pwd = await promptCryptoPassword();
    if (!pwd) {
        logConsole("Encriptação cancelada: Nenhuma password inserida.");
        return;
    }
    logConsole(`Iniciando encriptação AES para: ${path}`);
    try {
        const res = await callBackend('api_encriptar_com_password', path, pwd);
        if (res.success) {
            logConsole(`[SUCESSO] Ficheiro trancado: ${res.new_path}`);
            render_files(current_path);
        } else {
            logConsole(`[ERRO] Falha na encriptação: ${res.error}`);
        }
    } catch (e) {
        logConsole(`[ERRO FATAL] Motor de Criptografia falhou: ${e.message}`);
    }
}

async function decryptItem(path) {
    let pwd = await promptCryptoPassword();
    if (!pwd) {
        logConsole("Desencriptação cancelada: Nenhuma password inserida.");
        return;
    }
    logConsole(`Tentando desencriptar ficheiro seguro: ${path}`);
    try {
        const res = await callBackend('api_desencriptar_com_password', path, pwd);
        if (res.success) {
            logConsole(`[SUCESSO] Ficheiro restaurado: ${res.original_path}`);
            render_files(current_path);
        } else {
            logConsole(`[ERRO] Falha na desencriptação: ${res.error}`);
        }
    } catch (e) {
        logConsole(`[ERRO FATAL] Motor de Criptografia falhou: ${e.message}`);
    }
}

// 6. DATABASE & PROFILES INTEGRATION
function initDatabaseManager() {
    const refreshBtn = document.getElementById("btn-refresh-profiles");
    const form = document.getElementById("profile-form");

    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            logConsole("A sincronizar dados com o Postgres no Docker...");
            loadProfilesList();
        });
    }

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            const nome = document.getElementById("input-nome").value.trim();
            const cargo = document.getElementById("input-cargo").value.trim();
            const idade = parseInt(document.getElementById("input-idade").value);
            const notas = document.getElementById("input-notas").value.trim();
            const feedback = document.getElementById("form-feedback");

            feedback.className = "feedback-msg";
            feedback.textContent = "Gravando registo...";

            if (!backend) {
                feedback.className = "feedback-msg error";
                feedback.textContent = "Erro: Ambiente de comunicação desligado.";
                return;
            }

            logConsole(`Registando perfil: ${nome} [${cargo}]...`);

            try {
                const res = await callBackend('api_criar_perfil', nome, cargo, idade, notas);
                if (res.success) {
                    feedback.className = "feedback-msg success";
                    feedback.textContent = "Registo gravado com sucesso no Postgres!";
                    form.reset();
                    logConsole(`Perfil de '${nome}' guardado na tabela 'perfis'.`);

                    // Reload profiles list
                    loadProfilesList();
                } else {
                    feedback.className = "feedback-msg error";
                    feedback.textContent = `Erro: ${res.error}`;
                    logConsole(`Falha ao salvar perfil: ${res.error}`);
                }
            } catch (err) {
                feedback.className = "feedback-msg error";
                feedback.textContent = `Falha: ${err.message}`;
                logConsole(`Excepção ao submeter formulário: ${err.message}`);
            }
        });
    }
}

async function loadProfilesList() {
    const body = document.getElementById("profiles-list-body");
    if (!body) return;

    body.innerHTML = `<tr><td colspan="5" class="loading-td">Puxando perfis da base de dados...</td></tr>`;

    if (!backend) {
        body.innerHTML = `<tr><td colspan="5" class="loading-td" style="color:var(--neon-magenta)">Erro: Ambiente Eel indisponível.</td></tr>`;
        return;
    }

    try {
        const res = await callBackend('api_listar_perfis');
        if (res.success) {
            if (res.perfis.length === 0) {
                body.innerHTML = `<tr><td colspan="5" class="loading-td">Nenhum registo encontrado na tabela 'perfis'.</td></tr>`;
                logConsole("Tabela 'perfis' lida com sucesso (Vazia).");
                return;
            }

            body.innerHTML = "";
            res.perfis.forEach(perfil => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><span class="neon-magenta">${perfil.id}</span></td>
                    <td style="font-weight: bold; color: var(--text-bright)">${escapeHtml(perfil.nome)}</td>
                    <td><span class="neon-cyan">${escapeHtml(perfil.cargo)}</span></td>
                    <td>${perfil.idade}</td>
                    <td class="truncate" style="max-width: 250px" title="${escapeHtml(perfil.notas || '')}">${escapeHtml(perfil.notas || '-')}</td>
                `;
                body.appendChild(tr);
            });

            logConsole(`Sincronizados ${res.perfis.length} registos da base de dados.`);
        } else {
            body.innerHTML = `<tr><td colspan="5" class="loading-td" style="color:var(--neon-magenta)">Erro: ${res.error}</td></tr>`;
            logConsole(`Erro ao ler base de dados: ${res.error}`);
        }
    } catch (e) {
        body.innerHTML = `<tr><td colspan="5" class="loading-td" style="color:var(--neon-magenta)">Falha: ${e.message}</td></tr>`;
        logConsole(`Excepção ao ler base de dados: ${e.message}`);
    }
}

// Utility: Escape HTML to avoid XSS injections in HUD
function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// 7. REAL-TIME TELEMETRY HOOK
if (backend) {
    eel.expose(update_telemetry_ui);
}
function update_telemetry_ui(data) {
    // Update CPU
    const cpuVal = document.getElementById("tel-cpu-val");
    const cpuBar = document.getElementById("tel-cpu-bar");
    if (cpuVal && cpuBar) {
        cpuVal.textContent = data.cpu.toFixed(1) + "%";
        cpuBar.style.width = data.cpu + "%";
        if (data.cpu > 85) cpuBar.style.background = "var(--neon-magenta)";
        else cpuBar.style.background = "var(--neon-cyan)";
    }

    // Update RAM
    const ramVal = document.getElementById("tel-ram-val");
    const ramBar = document.getElementById("tel-ram-bar");
    if (ramVal && ramBar) {
        ramVal.textContent = data.ram.toFixed(1) + "%";
        ramBar.style.width = data.ram + "%";
        if (data.ram > 85) ramBar.style.background = "var(--neon-magenta)";
        else ramBar.style.background = "var(--neon-cyan)";
    }

    // Update Disk
    const diskVal = document.getElementById("tel-disk-val");
    const diskBar = document.getElementById("tel-disk-bar");
    if (diskVal && diskBar) {
        diskVal.textContent = data.disk.toFixed(1) + "%";
        diskBar.style.width = data.disk + "%";
    }

    // Update Temp
    const tempVal = document.getElementById("tel-temp-val");
    if (tempVal) {
        tempVal.textContent = data.temps;
    }
}

function updateImageViewer() {
    const img = document.getElementById("image-viewer-img");
    const pathDisplay = document.getElementById("image-viewer-path");
    const counterDisplay = document.getElementById("image-viewer-counter");
    const btnPrev = document.getElementById("btn-prev-image");
    const btnNext = document.getElementById("btn-next-image");

    if (!img || current_folder_images.length === 0) return;

    const currentItem = current_folder_images[current_image_index];

    // Show loading text
    const loadingText = document.getElementById('image-viewer-loading');
    if (loadingText) loadingText.style.display = 'block';

    // Wait for image to load to capture base dimensions before setting src
    img.onload = () => {
        img.dataset.baseWidth = img.clientWidth;
        img.dataset.baseHeight = img.clientHeight;
        if (loadingText) loadingText.style.display = 'none';
    };
    
    img.src = 'file:///' + currentItem.path.replace(/\\/g, '/');
    
    if (pathDisplay) {
        pathDisplay.textContent = currentItem.path;
    }
    
    if (counterDisplay) {
        counterDisplay.textContent = `[ ${current_image_index + 1} / ${current_folder_images.length} ]`;
    }

    if (btnPrev) {
        btnPrev.style.display = current_image_index > 0 ? "block" : "none";
    }
    
    if (btnNext) {
        btnNext.style.display = current_image_index < current_folder_images.length - 1 ? "block" : "none";
    }

    // Reset Zoom
    const zoomSlider = document.getElementById('image-viewer-zoom');
    const zoomVal = document.getElementById('image-viewer-zoom-val');
    if (zoomSlider && img) {
        zoomSlider.value = 100;
        if (zoomVal) zoomVal.value = 100;
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.maxWidth = '100%';
        img.style.maxHeight = '100%';
        img.style.flexShrink = '0';
    }
}
