import os
import sys
import platform
import pathlib
import requests
import psutil
import threading
import time
import ctypes
import subprocess
import shutil
import zipfile

# PYQT6 IMPORTS
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QObject, pyqtSlot, QVariant
from PyQt6.QtWebChannel import QWebChannel

# DEBUG HOOK PARA CAPTURAR CRASHES
def exception_hook(exctype, value, tb):
    print("\n" + "=" * 80)
    print("FATAL ERROR: A aplicação sofreu um crash inesperado!")
    import traceback
    traceback.print_exception(exctype, value, tb)
    print("=" * 80 + "\n")
    sys.exit(1)

sys.excepthook = exception_hook
import json

import subprocess
import shutil

try:
    # Garante que o Windows reconhece o ID do processo para separar o ícone do Chrome
    myappid = 'vexylo.dashboard.v1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    import base64
except ModuleNotFoundError:
    print("[!] AVISO: A biblioteca 'cryptography' não está instalada.")
    print("[!] O módulo de encriptação AES estará indisponível. Execute 'pip install cryptography'.")
    Fernet = None

def _derivar_chave(password: str) -> bytes:
    """Deriva uma chave estável de 32 bytes a partir da password usando um salt fixo do sistema."""
    if not Fernet: return b''
    salt = b'vexylo_secret_salt_123' # Salt estático para consistência de recuperação
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

# ----------------------------------------------------
# 0. ELEVAÇÃO DE PRIVILÉGIOS NO ARRANQUE
# ----------------------------------------------------
def check_and_elevate_privileges():
    system = platform.system()
    if system == 'Windows':
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            is_admin = False
            
        if not is_admin:
            print("[*] Requerendo privilégios de Administrador no Windows...")
            try:
                script = os.path.abspath(sys.argv[0])
                params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
            except Exception as e:
                print(f"[!] Falha na elevação: {e}")
            sys.exit()
    elif system == 'Linux':
        pass

# check_and_elevate_privileges()

def correr_como_root(comando):
    """Auxiliar para correr comandos específicos no Linux com root."""
    if platform.system() != "Linux":
        return None
    try:
        if shutil.which("pkexec"):
            return subprocess.run(["pkexec"] + comando, capture_output=True, text=True)
        else:
            return subprocess.run(["sudo", "-A"] + comando, capture_output=True, text=True)
    except Exception as e:
        return str(e)

# ----------------------------------------------------
# 1. SETUP & CONFIGURATION (CAMINHOS CORRIGIDOS)
# ----------------------------------------------------
# Define o caminho correto da pasta web de forma absoluta
current_dir = os.path.dirname(os.path.abspath(__file__))
web_dir = os.path.join(current_dir, 'web')

API_BASE_URL = "http://localhost:2060"

# Sessão global persistente (Mantém os cookies/tokens automaticamente para não ter de relogar)
api_session = requests.Session()

# ----------------------------------------------------
# 2. HANDSHAKE E AUTENTICAÇÃO COM API
# ----------------------------------------------------
def authenticate_api():
    """Verifica se o backend API está online e acessível."""
    try:
        # Apenas um ping para garantir que o Docker/API está online antes de continuar
        res = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        if res.status_code == 200:
            print("[*] Conexão com o Backend da API (Docker) estabelecida.")
            return True
        else:
            print(f"[!] Aviso na ligação: A API não retornou 200 OK (Código: {res.status_code})")
            return False
    except Exception as e:
        print(f"[!] Erro crítico ao conectar com a API: {e}")
        return False

def register_host_os():
    """Detecta o SO e Package Manager nativos e reporta à API já autenticada."""
    system = platform.system()
    distro_name = platform.release() if system == "Windows" else "Unknown Linux"
    package_manager = "winget/choco" if system == "Windows" else "N/A"
    
    if system == "Linux":
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro_name = line.split("=")[1].strip().strip('"')
                        break
            
            distro_lower = distro_name.lower()
            if distro_lower in ["arch", "manjaro", "endeavouros"]:
                package_manager = "pacman"
            elif distro_lower in ["ubuntu", "debian", "linuxmint", "pop"]:
                package_manager = "apt"
            elif distro_lower in ["fedora", "centos", "rhel", "almalinux", "rocky"]:
                package_manager = "dnf"
        except Exception:
            pass

    payload = {
        "os": system,
        "distro": distro_name,
        "package_manager": package_manager
    }
    
    try:
        # Usamos a api_session já autenticada para enviar o report com os headers/cookies de autorização embutidos
        res = api_session.post(f"{API_BASE_URL}/api/system/os", json=payload, timeout=3)
        if res.status_code == 200:
            print(f"[*] Host OS sincronizado com a API: {system} ({distro_name}) via {package_manager}")
        else:
            print(f"[!] Falha ao sincronizar OS: HTTP {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[!] Erro ao enviar dados do SO: {e}")

# ----------------------------------------------------
from PyQt6.QtCore import QTimer

def get_telemetry_data():
    """Recolhe as métricas de hardware (CPU, RAM, Disco) rapidamente."""
    try:
        # 3.1 Recolher Métricas
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        
        disk_path = 'C:\\' if platform.system() == 'Windows' else '/'
        try:
            disk = psutil.disk_usage(disk_path).percent
        except Exception:
            disk = 0.0
            
        temps_data = "N/A"
        if hasattr(psutil, "sensors_temperatures"):
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    first_sensor = list(temps.values())[0]
                    if first_sensor:
                        temps_data = f"{first_sensor[0].current}°C"
            except Exception:
                pass
                
        return {"cpu": cpu, "ram": ram, "disk": disk, "temps": temps_data}
    except Exception as e:
        return None

cpu_history = []
ram_history = []
last_api_post = time.time()



# ----------------------------------------------------
# 4. EXPOSIÇÃO DE FUNÇÕES AO FRONTEND ()
# ----------------------------------------------------



class VexyloBridge(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window

    @pyqtSlot(result=bool)
    def api_has_account(self):
        try:
            res = requests.get(f"{API_BASE_URL}/api/has-account", timeout=3)
            if res.status_code == 200:
                return res.json().get("has_account", False)
        except:
            pass
        return False

    @pyqtSlot(str, str, result=bool)
    def api_register_account(self, username, password):
        try:
            res = requests.post(f"{API_BASE_URL}/api/register", data={"username": username, "password": password}, timeout=3)
            if res.status_code == 200:
                return self.api_login_account(username, password)
        except:
            pass
        return False

    @pyqtSlot(str, str, result=bool)
    def api_login_account(self, username, password):
        try:
            res = api_session.post(f"{API_BASE_URL}/api/login", data={"username": username, "password": password}, timeout=3)
            return res.status_code == 200
        except:
            return False

    @pyqtSlot(str, result=bool)
    def api_verify_master_password(self, password):
        try:
            res = requests.get(f"{API_BASE_URL}/api/has-account", timeout=3)
            if res.status_code == 200:
                username = res.json().get("username")
                if username:
                    return self.api_login_account(username, password)
        except:
            pass
        return False

    @pyqtSlot(result=bool)
    def api_has_api_key(self):
        return os.path.exists('local_apikey.json')

    @pyqtSlot(str, result=bool)
    def api_save_api_key(self, key):
        import json
        try:
            with open('local_apikey.json', 'w') as f:
                json.dump({"api_key": key}, f)
            return True
        except Exception:
            return False

    @pyqtSlot(result=bool)
    def api_verify_api_key(self):
        import json
        try:
            if not os.path.exists('local_apikey.json'):
                return False
            with open('local_apikey.json', 'r') as f:
                data = json.load(f)
                key = data.get("api_key")
            
            if not key:
                return False
                
            res = requests.get(f"{API_BASE_URL}/api/verify-key", headers={"X-API-Key": key}, timeout=3)
            if res.status_code == 200:
                # Se for válida, injeta no api_session global para todos os futuros pedidos
                api_session.headers.update({"X-API-Key": key})
                return True
        except Exception:
            pass
        return False

    @pyqtSlot(result='QVariant')
    def api_get_vaults(self):
        try:
            res = api_session.get(f"{API_BASE_URL}/api/vaults", timeout=3)
            if res.status_code == 200:
                return res.json()
        except:
            pass
        return []

    @pyqtSlot(str, str, str, str, result=bool)
    def api_register_vault(self, name, path, security_type, password):
        import zipfile
        vaults = self.api_get_vaults()
        for v in vaults:
            if v["name"] == name:
                return False
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            empty_zip_path = path + ".empty.zip"
            with zipfile.ZipFile(empty_zip_path, 'w') as zf:
                pass
            
            chave = _derivar_chave(password)
            f_suite = Fernet(chave)
            with open(empty_zip_path, 'rb') as f:
                raw_data = f.read()
            encrypted = f_suite.encrypt(raw_data)
            
            with open(path, 'wb') as f:
                f.write(encrypted)
            os.remove(empty_zip_path)
        except Exception:
            return False

        try:
            payload = {
                "name": name,
                "path": path,
                "security_type": security_type
            }
            res = api_session.post(f"{API_BASE_URL}/api/vaults", json=payload, timeout=3)
            return res.status_code in [200, 201]
        except Exception:
            return False

    @pyqtSlot(str, result=bool)
    def open_native_file(self, filepath):
        """Abre ficheiros com a aplicação nativa do SO (ex: Visualizador de Imagens)"""
        try:
            if platform.system() == "Windows":
                os.startfile(filepath)
            elif platform.system() == "Darwin":
                subprocess.call(["open", filepath])
            else:
                subprocess.call(["xdg-open", filepath])
            return True
        except Exception as e:
            print(f"[!] Erro ao abrir ficheiro nativo: {e}")
            return False

    @pyqtSlot(str, str, result='QVariant')
    def api_unlock_vault(self, password, keyfile_path):
        return self.api_mount_vault(password)

    @pyqtSlot(result=bool)
    def api_lock_vault(self):
        res = self.api_unmount_vault()
        return res.get("success", False)

    @pyqtSlot(result='QVariant')
    def obter_info_sistema(self):
        """Retorna informações do sistema operativo para o Monitor"""
        try:
            return {
                "os_name": platform.system(),
                "os_release": platform.release(),
                "os_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor() or "Processador Desconhecido",
                "cpu_cores": os.cpu_count() or 1,
                "python_version": platform.python_version(),
                "home_dir": str(pathlib.Path.home().absolute())
            }
        except Exception as e:
            return {"error": str(e)}

    
    @pyqtSlot(result='QVariant')
    def listar_ficheiros_home(self):
        """Lista os ficheiros na pasta Home do utilizador"""
        try:
            home_path = pathlib.Path.home()
            items = []
            for item in home_path.iterdir():
                if item.name.startswith('.'):
                    continue
                item_type = "Pasta" if item.is_dir() else "Ficheiro"
                size_kb = 0
                if item.is_file():
                    try:
                        size_kb = round(item.stat().st_size / 1024, 1)
                    except Exception:
                        pass
                items.append({
                    "nome": item.name,
                    "tipo": item_type,
                    "tamanho": f"{size_kb} KB" if item_type == "Ficheiro" else "-"
                })
            items.sort(key=lambda x: (x["tipo"] != "Pasta", x["nome"].lower()))
            return {"success": True, "home_dir": str(home_path.absolute()), "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}

    
    @pyqtSlot(result='QVariant')
    def api_listar_perfis(self):
        """Puxa todos os perfis da API (Dossiers) no Docker e mapeia para o frontend"""
        try:
            res = api_session.get(f"{API_BASE_URL}/api/dossiers", timeout=3)
            if res.status_code == 200:
                dossiers = res.json()
                perfis = []
                for d in dossiers:
                    perfis.append({
                        "id": d["id"],
                        "nome": d["name"],
                        "cargo": d.get("role") or "-",
                        "idade": "-", 
                        "notas": d.get("notes") or ""
                    })
                return {"success": True, "perfis": perfis}
            return {"success": False, "error": f"Erro HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            return {"success": False, "error": f"Erro de conexão com API: {str(e)}"}

    
    @pyqtSlot(str, str, str, str, result='QVariant')
    def api_criar_perfil(self, nome, cargo, idade, notas):
        """Guarda um novo perfil na base de dados através da API (Dossiers)"""
        try:
            payload = {
                "name": nome,
                "role": cargo,
                "notes": f"Idade: {idade}. {notas}"
            }
            res = api_session.post(f"{API_BASE_URL}/api/dossiers", json=payload, timeout=3)
            if res.status_code in [200, 201]:
                return {"success": True, "perfil": res.json()}
            return {"success": False, "error": f"Erro HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            return {"success": False, "error": f"Erro de conexão com API: {str(e)}"}


    
    @pyqtSlot(result='QVariant')
    def obter_status_api(self):
        """Verifica o status base da API localmente"""
        try:
            res = requests.get(f"{API_BASE_URL}/", timeout=0.1)
            if res.status_code == 200:
                return {"online": True, "data": "API Vexylo Online"}
            return {"online": False, "error": f"Erro HTTP {res.status_code}"}
        except Exception as e:
            return {"online": False, "error": "API Offline (Connection Refused)"}

    
    @pyqtSlot(result='QVariant')
    def api_listar_dossiers(self):
        """Puxa a lista de dossiers pela api_session autenticada"""
        try:
            res = api_session.get(f"{API_BASE_URL}/api/dossiers", timeout=3)
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            return {"success": False, "error": f"Erro HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            return {"success": False, "error": f"Erro de conexão com API: {str(e)}"}

    
    @pyqtSlot(str, result='QVariant')
    def api_criar_nota(self, conteudo):
        """Cria uma nota de sistema através da API utilizando a sessão mestra"""
        try:
            payload = {"content": conteudo}
            res = api_session.post(f"{API_BASE_URL}/api/notes", json=payload, timeout=3)
            if res.status_code in [200, 201]:
                return {"success": True, "nota": res.json()}
            return {"success": False, "error": f"Erro HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            return {"success": False, "error": f"Erro de conexão com API: {str(e)}"}

    # ----------------------------------------------------
    # 5. GESTOR DE FICHEIROS INTERNO ()
    # ----------------------------------------------------

    @pyqtSlot(str, result='QVariant')
    def api_toggle_hide_item(self, path):
        try:
            res = api_session.post(f"{API_BASE_URL}/api/file-metadata/toggle-hidden?path={path}", timeout=3)
            if res.status_code == 200:
                data = res.json()
                msg = "Item ocultado." if data.get("is_hidden") else "Item visível."
                return {"success": True, "msg": msg}
        except Exception as e:
            pass
        return {"success": False, "msg": "Erro de comunicação."}

    @pyqtSlot(str, result='QVariant')
    def api_toggle_pin(self, path):
        try:
            res = api_session.post(f"{API_BASE_URL}/api/file-metadata/toggle-pin?path={path}", timeout=3)
            if res.status_code == 200:
                data = res.json()
                msg = "PIN adicionado." if data.get("is_pinned") else "PIN removido."
                return {"success": True, "msg": msg}
        except Exception as e:
            pass
        return {"success": False, "msg": "Erro de comunicação."}

    @pyqtSlot(str, result='QVariant')
    def api_toggle_favorite(self, path):
        try:
            res = api_session.post(f"{API_BASE_URL}/api/file-metadata/toggle-favorite?path={path}", timeout=3)
            if res.status_code == 200:
                data = res.json()
                msg = "Favorito adicionado." if data.get("is_favorite") else "Favorito removido."
                return {"success": True, "msg": msg}
        except Exception as e:
            pass
        return {"success": False, "msg": "Erro de comunicação."}

    @pyqtSlot(result='QVariant')
    def api_get_user_shortcuts(self):
        try:
            res = api_session.get(f"{API_BASE_URL}/api/file-metadata", timeout=3)
            if res.status_code == 200:
                items = res.json()
                pins = [item["path"] for item in items if item["is_pinned"]]
                favs = [item["path"] for item in items if item["is_favorite"]]
                return {
                    "success": True, 
                    "pins": pins,
                    "favs": favs
                }
        except Exception as e:
            pass
        return {"success": False, "pins": [], "favs": []}

    
    @pyqtSlot(result='QVariant')
    def get_home_directory(self):
        """Retorna o diretório home absoluto do utilizador"""
        return str(pathlib.Path.home().absolute())

    # --- VEXYLO VAULT (VIRTUAL MOUNT) ---
    import zipfile
    
    @pyqtSlot(str, str, result='QVariant')
    def api_create_vexylo_vault(self, folder_path, password):
        if not os.path.isdir(folder_path):
            return {"success": False, "error": "Caminho não é uma pasta"}
        try:
            chave = _derivar_chave(password)
            f_suite = Fernet(chave)

            # 1. Zip the folder
            zip_path = folder_path + ".tmp.zip"
            shutil.make_archive(folder_path + ".tmp", 'zip', folder_path)

            # 2. Encrypt the zip
            with open(zip_path, 'rb') as f:
                raw_data = f.read()
            encrypted_data = f_suite.encrypt(raw_data)

            # 3. Save as .vexylo
            vault_path = folder_path + ".vexylo"
            with open(vault_path, 'wb') as f:
                f.write(encrypted_data)

            # 4. Clean up
            os.remove(zip_path)
            shutil.rmtree(folder_path)

            return {"success": True, "vault_path": vault_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _emit_progress(self, pct, phase_msg, file_msg=""):
        # Safe escaping for JS
        pm = phase_msg.replace("'", "\\'")
        fm = file_msg.replace("'", "\\'")
        script = f"if (typeof ui_update_smart_progress === 'function') ui_update_smart_progress({pct}, '{pm}', '{fm}');"
        self.window.browser.page().runJavaScript(script)

    @pyqtSlot(str, str, str, result='QVariant')
    def api_mount_vexylo_vault(self, name, vault_path, password):
        if not os.path.isfile(vault_path) or not vault_path.endswith('.vexylo'):
            return {"success": False, "error": "Caminho não é um cofre Vexylo válido"}
        
        self.window.browser.page().runJavaScript(f"if (typeof ui_show_smart_progress === 'function') ui_show_smart_progress('[ UNLOCKING VAULT: {name} ]');")
        self._emit_progress(0, "PHASE 1: DESENCRIPTAÇÃO", "A Ler Ficheiro Encriptado...")
        
        try:
            chave = _derivar_chave(password)
            f_suite = Fernet(chave)

            # 1. Read and decrypt
            with open(vault_path, 'rb') as f:
                encrypted_data = f.read()
            
            self._emit_progress(10, "PHASE 1: DESENCRIPTAÇÃO", "A Desencriptar Bloco de Dados (AES-256)...")
            
            try:
                decrypted_data = f_suite.decrypt(encrypted_data)
            except Exception:
                self.window.browser.page().runJavaScript("if (typeof ui_hide_smart_progress === 'function') ui_hide_smart_progress();")
                return {"success": False, "error": "Password incorreta ou cofre corrompido."}

            self._emit_progress(25, "PHASE 2: PREPARAÇÃO I/O", "A Preparar Memória Virtual...")

            # 2. Save decrypted to tmp zip
            tmp_zip = vault_path + ".tmp.zip"
            with open(tmp_zip, 'wb') as f:
                f.write(decrypted_data)

            # 3. Extract zip to hidden mount folder with Smart Chunking
            home_dir = os.path.expanduser("~")
            mounts_dir = os.path.join(home_dir, ".vexylo_mounts")
            os.makedirs(mounts_dir, exist_ok=True)
            
            folder_name = name
            mount_path = os.path.join(mounts_dir, folder_name)
            
            if os.path.exists(mount_path):
                shutil.rmtree(mount_path)
            os.makedirs(mount_path)

            with zipfile.ZipFile(tmp_zip, 'r') as zip_ref:
                file_list = zip_ref.infolist()
                total_files = len(file_list)
                
                # Phase 2 starts at 25% and goes up to 100%
                for i, file_info in enumerate(file_list):
                    zip_ref.extract(file_info, mount_path)
                    
                    if total_files > 0:
                        chunk_pct = 25 + ((i + 1) / total_files) * 75
                        self._emit_progress(chunk_pct, "PHASE 2: PROCESSAMENTO (EXTRAÇÃO)", f"{file_info.filename}")
            
            os.remove(tmp_zip)
            
            self._emit_progress(100, "CONCLUÍDO", "Cofre montado com segurança.")
            import time
            time.sleep(0.5) # Give UI time to show 100%
            self.window.browser.page().runJavaScript("if (typeof ui_hide_smart_progress === 'function') ui_hide_smart_progress();")
            
            return {"success": True, "mount_path": mount_path}
        except Exception as e:
            self.window.browser.page().runJavaScript("if (typeof ui_hide_smart_progress === 'function') ui_hide_smart_progress();")
            return {"success": False, "error": str(e)}

    @pyqtSlot(str, str, str, str, result='QVariant')
    def api_transfer_to_vault(self, target_path, vault_name, vault_path, password):
        if not os.path.exists(target_path):
            return {"success": False, "error": "Alvo não existe"}
            
        self.window.browser.page().runJavaScript(f"if (typeof ui_show_smart_progress === 'function') ui_show_smart_progress('[ TRANSFERRING TO: {vault_name} ]');")
        self._emit_progress(0, "PHASE 1: DESENCRIPTAÇÃO", "A Inicializar...")
        
        try:
            chave = _derivar_chave(password)
            f_suite = Fernet(chave)

            # 1. Decrypt existing vault
            with open(vault_path, 'rb') as f:
                encrypted_data = f.read()
            self._emit_progress(10, "PHASE 1: DESENCRIPTAÇÃO", "A Desencriptar Cofre...")
            try:
                decrypted_data = f_suite.decrypt(encrypted_data)
            except Exception:
                self.window.browser.page().runJavaScript("if (typeof ui_hide_smart_progress === 'function') ui_hide_smart_progress();")
                return {"success": False, "error": "Password incorreta ou cofre corrompido."}

            self._emit_progress(25, "PHASE 2: I/O & CHUNKING", "A Preparar Ficheiros...")

            # 2. Extract decrypted data into a tmp folder
            home_dir = os.path.expanduser("~")
            tmp_mount_dir = os.path.join(home_dir, ".vexylo_tmp_transfer_" + vault_name)
            if os.path.exists(tmp_mount_dir):
                shutil.rmtree(tmp_mount_dir)
            os.makedirs(tmp_mount_dir)
            
            tmp_zip_read = vault_path + ".tmp.read.zip"
            with open(tmp_zip_read, 'wb') as f:
                f.write(decrypted_data)
            
            with zipfile.ZipFile(tmp_zip_read, 'r') as zip_ref:
                zip_ref.extractall(tmp_mount_dir)
            os.remove(tmp_zip_read)

            # 3. Move target_path into the extracted folder
            dest = os.path.join(tmp_mount_dir, os.path.basename(target_path))
            if os.path.isdir(target_path):
                if os.path.exists(dest): shutil.rmtree(dest)
                shutil.copytree(target_path, dest)
            else:
                shutil.copy2(target_path, dest)

            # 4. Zip the tmp folder (This is where the heavy Smart Chunking >=50% happens)
            zip_path = tmp_mount_dir + ".tmp.write.zip"
            total_size = 0
            all_files = []
            for root, dirs, files in os.walk(tmp_mount_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    total_size += os.path.getsize(fp)
                    all_files.append(fp)
            
            processed_size = 0
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for fp in all_files:
                    arcname = os.path.relpath(fp, tmp_mount_dir)
                    zipf.write(fp, arcname)
                    processed_size += os.path.getsize(fp)
                    if total_size > 0:
                        # Phase 2 takes 50% (from 25% to 75%)
                        chunk_pct = 25 + (processed_size / total_size) * 50
                        self._emit_progress(chunk_pct, "PHASE 2: PROCESSAMENTO (COMPRESSÃO)", arcname)

            self._emit_progress(75, "PHASE 3: ENCRIPTAÇÃO", "A Ler Bloco de Dados Zipado...")

            # 5. Encrypt the new zip (Takes up another 25%, to 100%)
            with open(zip_path, 'rb') as f:
                raw_data = f.read()
                
            self._emit_progress(85, "PHASE 3: ENCRIPTAÇÃO", "A Encriptar Bloco (AES-256)...")
            encrypted_data = f_suite.encrypt(raw_data)

            self._emit_progress(95, "PHASE 3: ESCRITA DISCO", "A Gravar Cofre Permanente...")
            with open(vault_path, 'wb') as f:
                f.write(encrypted_data)

            # 6. Clean up
            os.remove(zip_path)
            shutil.rmtree(tmp_mount_dir)
            
            # Delete original file safely since it was moved to vault
            if os.path.isdir(target_path):
                shutil.rmtree(target_path)
            else:
                os.remove(target_path)

            self._emit_progress(100, "CONCLUÍDO", "Ficheiros guardados em segurança no cofre.")
            import time
            time.sleep(0.5)
            self.window.browser.page().runJavaScript("if (typeof ui_hide_smart_progress === 'function') ui_hide_smart_progress();")

            return {"success": True, "vault_path": vault_path}
        except Exception as e:
            self.window.browser.page().runJavaScript("if (typeof ui_hide_smart_progress === 'function') ui_hide_smart_progress();")
            return {"success": False, "error": str(e)}

    @pyqtSlot(str, str, str, str, result='QVariant')
    def api_unmount_vexylo_vault(self, name, mount_path, vault_path, password):
        if not os.path.exists(mount_path):
            return {"success": False, "error": "Cofre não está montado"}
        
        self.window.browser.page().runJavaScript(f"if (typeof ui_show_smart_progress === 'function') ui_show_smart_progress('[ LOCKING VAULT: {name} ]');")
        self._emit_progress(0, "PHASE 1: PREPARAÇÃO", "A Inicializar Compressão...")
        
        try:
            chave = _derivar_chave(password)
            f_suite = Fernet(chave)

            # 1. Zip the mount folder manually for Smart Chunking
            zip_path = mount_path + ".tmp.zip"
            
            # Count total files for math
            total_size = 0
            all_files = []
            for root, dirs, files in os.walk(mount_path):
                for f in files:
                    fp = os.path.join(root, f)
                    total_size += os.path.getsize(fp)
                    all_files.append(fp)
            
            processed_size = 0
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for fp in all_files:
                    arcname = os.path.relpath(fp, mount_path)
                    zipf.write(fp, arcname)
                    processed_size += os.path.getsize(fp)
                    if total_size > 0:
                        # Phase 2 (Zipping) takes 50% of the progress bar (from 0 to 50%)
                        chunk_pct = (processed_size / total_size) * 50
                        self._emit_progress(chunk_pct, "PHASE 2: PROCESSAMENTO (COMPRESSÃO)", arcname)

            self._emit_progress(50, "PHASE 3: ENCRIPTAÇÃO", "A Ler Bloco de Dados Zipado...")

            # 2. Encrypt the zip (Takes up another 25%, to 75%)
            with open(zip_path, 'rb') as f:
                raw_data = f.read()
                
            self._emit_progress(75, "PHASE 3: ENCRIPTAÇÃO", "A Encriptar Bloco (AES-256)...")
            encrypted_data = f_suite.encrypt(raw_data)

            # 3. Save as .vexylo (Final 25%, to 100%)
            self._emit_progress(85, "PHASE 3: ESCRITA DISCO", "A Gravar Cofre Permanente...")
            with open(vault_path, 'wb') as f:
                f.write(encrypted_data)

            # 4. Clean up
            os.remove(zip_path)
            shutil.rmtree(mount_path)

            self._emit_progress(100, "CONCLUÍDO", "Cofre trancado em segurança.")
            import time
            time.sleep(0.5)
            self.window.browser.page().runJavaScript("if (typeof ui_hide_smart_progress === 'function') ui_hide_smart_progress();")

            return {"success": True, "vault_path": vault_path}
        except Exception as e:
            self.window.browser.page().runJavaScript("if (typeof ui_hide_smart_progress === 'function') ui_hide_smart_progress();")
            return {"success": False, "error": str(e)}

    @pyqtSlot(str, str, result='QVariant')
    def list_directory_contents(self, target_path, show_hidden=False):
        """Lista ficheiros e pastas de um diretório específico ou interior de ZIP"""
    
        try:
            normalized_path = target_path.replace('\\', '/')
            zip_file_path = None
            internal_path = ""
        
            parts = normalized_path.split('/')
            for i, part in enumerate(parts):
                if part.lower().endswith('.zip'):
                    zip_file_path = '/'.join(parts[:i+1])
                    internal_path = '/'.join(parts[i+1:])
                    break
                
            if zip_file_path and os.path.isfile(zip_file_path):
                import zipfile
                items_dict = {}
                prefix = internal_path + '/' if internal_path else ''
            
                with zipfile.ZipFile(zip_file_path, 'r') as zf:
                    for info in zf.infolist():
                        if info.filename.startswith(prefix):
                            rest = info.filename[len(prefix):]
                            if not rest:
                                continue
                            subparts = rest.split('/')
                            top_level = subparts[0]
                        
                            is_dir = (len(subparts) > 1 and subparts[1] != "") or info.is_dir()
                            if top_level not in items_dict:
                                items_dict[top_level] = {
                                    "name": top_level,
                                    "is_dir": is_dir,
                                    "size": info.file_size,
                                    "extension": pathlib.Path(top_level).suffix if not is_dir else ""
                                }
                            else:
                                if is_dir:
                                    items_dict[top_level]["is_dir"] = True
            
                hidden_vault = []
                try:
                    res = api_session.get(f"{API_BASE_URL}/api/file-metadata", timeout=3)
                    if res.status_code == 200:
                        hidden_vault = [item["path"] for item in res.json() if item["is_hidden"]]
                except:
                    pass
                items = []
                for name, data in items_dict.items():
                    virtual_path = f"{zip_file_path}/{prefix}{name}".rstrip('/')
                    if not show_hidden and virtual_path in hidden_vault:
                        continue
                
                    is_d = data["is_dir"]
                    size_b = data["size"]
                    size_mb = round(size_b / (1024 * 1024), 2)
                    size_kb = round(size_b / 1024, 1)
                    tamanho = "---" if is_d else (f"{size_mb} MB" if size_mb >= 1 else f"{size_kb} KB")
                
                    items.append({
                        "name": name,
                        "is_dir": is_d,
                        "size": tamanho,
                        "path": virtual_path,
                        "extension": data["extension"]
                    })
            
                items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
                return {"success": True, "path": target_path, "items": items}
            
            path = pathlib.Path(target_path)
            if not path.exists() or not path.is_dir():
                return {"success": False, "error": "Caminho inválido ou não é um diretório."}
            
            hidden_vault = []
            try:
                res = api_session.get(f"{API_BASE_URL}/api/file-metadata", timeout=3)
                if res.status_code == 200:
                    hidden_vault = [item["path"] for item in res.json() if item["is_hidden"]]
            except:
                pass
            items = []
            for item in path.iterdir():
                try:
                    item_path_str = str(item.absolute())
                    if not show_hidden and item_path_str in hidden_vault:
                        continue
                    
                    stat = item.stat()
                    item_type = "Pasta" if item.is_dir() else "Ficheiro"
                    size_mb = round(stat.st_size / (1024 * 1024), 2) if item.is_file() else 0
                    size_kb = round(stat.st_size / 1024, 1) if item.is_file() else 0
                
                    if item_type == "Ficheiro":
                        tamanho = f"{size_mb} MB" if size_mb >= 1 else f"{size_kb} KB"
                    else:
                        tamanho = "---"
                    
                    items.append({
                        "name": item.name,
                        "is_dir": item.is_dir(),
                        "size": tamanho,
                        "path": str(item.absolute()),
                        "extension": item.suffix if item.is_file() else ""
                    })
                except Exception:
                    pass
                
            items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
            return {"success": True, "path": str(path.absolute()), "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}

    
    @pyqtSlot(str, str, str, result='QVariant')
    def api_extrair_zip_avancado(self, zip_path, target_dir, criar_subpasta):
        try:
            if not os.path.exists(zip_path):
                return {"success": False, "error": "Arquivo ZIP não encontrado."}
            
            # CORREÇÃO CRUCIAL: Confia no caminho que o utilizador digitou.
            # Não importa se existe ou não, o Python vai criar a estrutura.
            final_output_dir = target_dir.strip()
        
            # Se o utilizador pediu para criar a subpasta com o nome do arquivo ZIP
            if criar_subpasta:
                nome_zip = os.path.splitext(os.path.basename(zip_path))[0]
                # Evita duplicar se o utilizador já escreveu o nome da pasta no input
                if not final_output_dir.endswith(nome_zip):
                    final_output_dir = os.path.join(final_output_dir, nome_zip)
        
            # Cria recursivamente todas as pastas do caminho (ex: se 'Klg' não existir, cria-a)
            os.makedirs(final_output_dir, exist_ok=True)
        
            # Executa a extração para o caminho final garantido
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(final_output_dir)
            
            return {"success": True, "extracted_to": final_output_dir}
        except Exception as e:
            return {"success": False, "error": str(e)}

    
    @pyqtSlot(str, str, result='QVariant')
    def api_criar_pasta(self, current_dir, folder_name):
        try:
            if not folder_name.strip():
                return {"success": False, "error": "Nome da pasta inválido."}
            target_path = os.path.join(current_dir, folder_name.strip())
            os.makedirs(target_path, exist_ok=False) # Falha se já existir
            return {"success": True}
        except FileExistsError:
            return {"success": False, "error": "Essa pasta já existe!"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    
    @pyqtSlot(str, str, result='QVariant')
    def api_criar_ficheiro(self, current_dir, file_name):
        try:
            if not file_name.strip():
                return {"success": False, "error": "Nome do ficheiro inválido."}
            target_path = os.path.join(current_dir, file_name.strip())
        
            # Cria o ficheiro vazio de forma segura
            with open(target_path, 'x', encoding='utf-8') as f:
                pass
            
            return {"success": True, "full_path": target_path}
        except FileExistsError:
            return {"success": False, "error": "Esse ficheiro já existe!"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    
    @pyqtSlot(str, result='QVariant')
    def api_criar_zip(self, target_path):
        """Pega num ficheiro ou pasta e comprime-o num ficheiro .zip no mesmo diretório"""
        try:
            if not os.path.exists(target_path):
                return {"success": False, "error": "O caminho alvo não existe."}
            
            # Define o nome do ficheiro zip de saída (ex: pasta.zip ou documento.txt.zip)
            zip_output_path = target_path + ".zip"
        
            import zipfile
            with zipfile.ZipFile(zip_output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.isdir(target_path):
                    # Se for uma pasta, caminha por dentro dela e adiciona todos os ficheiros
                    for root, dirs, files in os.walk(target_path):
                        for file in files:
                            full_path = os.path.join(root, file)
                            # Cria um caminho relativo dentro do ZIP para manter a estrutura de pastas
                            relative_path = os.path.relpath(full_path, os.path.dirname(target_path))
                            zipf.write(full_path, relative_path)
                else:
                    # Se for apenas um ficheiro, adiciona-o diretamente
                    zipf.write(target_path, os.path.basename(target_path))
                
            return {"success": True, "zip_path": zip_output_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    
    @pyqtSlot(str, result='QVariant')
    def api_calcular_tamanho_pasta(self, folder_path):
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
            # Formatar
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total_size < 1024.0:
                    return f"{total_size:.1f} {unit}"
                total_size /= 1024.0
            return f"{total_size:.1f} TB"
        except Exception as e:
            return "Erro"

    
    @pyqtSlot(str, str, str, result='QVariant')
    def execute_file_system_action(self, action_type, source_path, destination_path=None):
        """Manipula ficheiros: delete, rename, move, com fallback para root no Linux"""
        try:
            path = pathlib.Path(source_path)
            if not path.exists():
                return {"success": False, "error": "Ficheiro/Pasta não existe."}
            
            system = platform.system()
        
            try:
                if action_type == 'delete':
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                elif action_type == 'rename' or action_type == 'move':
                    if not destination_path:
                        return {"success": False, "error": "destination_path não especificado."}
                    shutil.move(str(path), destination_path)
                else:
                    return {"success": False, "error": "Ação inválida."}
                
                return {"success": True, "message": f"Ação '{action_type}' executada com sucesso."}
            
            except PermissionError:
                if system == 'Windows':
                    return {"success": False, "error": "Acesso Negado (Ficheiro em uso ou falta de privilégios)."}
                elif system == 'Linux':
                    if action_type == 'delete':
                        res = correr_como_root(["rm", "-rf", str(path)])
                    elif action_type == 'rename' or action_type == 'move':
                        res = correr_como_root(["mv", str(path), destination_path])
                
                    if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
                        return {"success": True, "message": f"Ação '{action_type}' executada com elevação de privilégios."}
                    else:
                        err_msg = res.stderr if isinstance(res, subprocess.CompletedProcess) else res
                        return {"success": False, "error": f"Falha com elevação de privilégios: {err_msg}"}
                else:
                    return {"success": False, "error": "Permissão negada. SO não suporta fallback automático."}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    
    @pyqtSlot(str, str, result='QVariant')
    def api_renomear_item(self, old_path, new_name):
        """Renomeia um item e garante elevação de privilégios via fallback interno se necessário"""
        try:
            path = pathlib.Path(old_path)
            if not path.exists():
                return {"success": False, "error": "O ficheiro origem não foi encontrado."}
            
            new_path = path.parent / new_name
            # Utiliza o motor partilhado que já possui suporte Linux Root Bypass e Windows Fallback
            return execute_file_system_action('rename', str(path), str(new_path))
        except Exception as e:
            return {"success": False, "error": str(e)}

    
    @pyqtSlot(str, str, result='QVariant')
    def api_encriptar_com_password(self, file_path, password):
        if not Fernet:
             return {"success": False, "error": "Módulo de encriptação indisponível. Instale 'cryptography'."}
        try:
            if file_path.endswith('.batlock') or not password:
                return {"success": False, "error": "Parâmetros inválidos."}
            
            # 1. Encriptar o ficheiro localmente
            chave = _derivar_chave(password)
            f_suite = Fernet(chave)
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            encrypted_data = f_suite.encrypt(raw_data)
            new_path = file_path + '.batlock'
            with open(new_path, 'wb') as f:
                f.write(encrypted_data)
            os.remove(file_path)
        
            # 2. Enviar BACKUP DE SEGURANÇA para a API em background (Usa a api_session ativa)
            # Envia para a rota de configurações ou logs da API o destino e a password
            payload = {
                "file_path": new_path,
                "recovery_key": password,
                "status": "ENCRYPTED"
            }
            try:
                # Nota: Garante que a API aceita este payload ou adapta para a nossa rota '/api/system/logs'
                api_session.post(f"{API_BASE_URL}/api/system/logs", json={"cpu_avg": 0, "ram_avg": 0, "os_target": f"ENC:{new_path}:{password}"}, timeout=3)
            except Exception:
                pass # Não bloqueia o fluxo se a API falhar o log
            
            return {"success": True, "new_path": new_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    
    @pyqtSlot(str, str, result='QVariant')
    def api_desencriptar_com_password(self, file_path, password):
        if not Fernet:
             return {"success": False, "error": "Módulo de encriptação indisponível. Instale 'cryptography'."}
        try:
            if not file_path.endswith('.batlock') or not password:
                return {"success": False, "error": "Ficheiro inválido."}
            
            chave = _derivar_chave(password)
            f_suite = Fernet(chave)
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = f_suite.decrypt(encrypted_data)
            original_path = file_path.replace('.batlock', '')
            with open(original_path, 'wb') as f:
                f.write(decrypted_data)
            os.remove(file_path)
        
            return {"success": True, "original_path": original_path}
        except Exception:
            return {"success": False, "error": "PASSWORD INCORRETA. Acesso negado pelo sistema."}

    
    @pyqtSlot(str, result='QVariant')
    def read_file_content(self, file_path):
        """Lê o conteúdo de um ficheiro de texto"""
        try:
            path = pathlib.Path(file_path)
            if not path.exists() or not path.is_file():
                return {"success": False, "error": "Ficheiro não encontrado."}
            
            system = platform.system()
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {"success": True, "content": content}
            except PermissionError:
                if system == 'Windows':
                    return {"success": False, "error": "Acesso Negado."}
                elif system == 'Linux':
                    res = correr_como_root(["cat", str(path)])
                    if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
                        return {"success": True, "content": res.stdout}
                    else:
                        return {"success": False, "error": "Falha de permissões (root cat)."}
                else:
                    return {"success": False, "error": "Acesso Negado."}
            except UnicodeDecodeError:
                return {"success": False, "error": "O ficheiro não é um texto válido (UTF-8)."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    
    @pyqtSlot(str, str, result='QVariant')
    def save_file_content(self, file_path, text_content):
        """Grava texto num ficheiro, com fallback root para Linux"""
        try:
            path = pathlib.Path(file_path)
            system = platform.system()
        
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                return {"success": True}
            except PermissionError:
                if system == 'Windows':
                    return {"success": False, "error": "Acesso Negado ao guardar (Falta de privilégios)."}
                elif system == 'Linux':
                    tmp_path = path.parent / f".tmp_root_{path.name}"
                    try:
                        # Tenta escrever localmente primeiro (se a pasta permitir, falhou apenas no overwrite do ficheiro)
                        with open(tmp_path, 'w', encoding='utf-8') as f:
                            f.write(text_content)
                        res = correr_como_root(["mv", str(tmp_path), str(path)])
                        if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
                            return {"success": True}
                        else:
                            # Se não conseguir escrever na pasta (tmp falhou na linha open), o catch tratará disso
                            return {"success": False, "error": "Falha ao gravar com root (mv failed)."}
                    except Exception:
                        # Falha extrema, não temos permissões na própria diretoria. Usar echo pipe sudo tee
                        import shlex
                        safe_content = shlex.quote(text_content)
                        res = correr_como_root(["sh", "-c", f"echo {safe_content} | sudo -A tee {str(path)} > /dev/null"])
                        if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
                            return {"success": True}
                        else:
                            return {"success": False, "error": "Erro crítico no bypass de gravação Root."}
                else:
                    return {"success": False, "error": "Acesso Negado."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ----------------------------------------------------
    # 6. INICIALIZAÇÃO DO MOTOR PRINCIPAL
    # ----------------------------------------------------
    if __name__ == '__main__':
        print("==================================================")
        print(" INICIANDO VEXYLO DASHBOARD UPLINK ")
        print(f" URL Alvo: {API_BASE_URL}")
        print("==================================================")
    
        # 1. Faz o handshake e regista os cookies mestres na api_session
        if authenticate_api():
            # 2. Regista o Sistema na API
            register_host_os()
        
            # A Telemetria será iniciada como QTimer dentro da Main Window
            print("[*] Telemetria pronta para arrancar via GUI Timer.")
        else:
            print("[!] AVISO: A API parece estar offline ou as credenciais falharam.")
            print("[!] O Desktop App vai iniciar em modo de fallback, as chamadas remotas protegidas falharão.")
    
        print("\n[*] Lançando Interface Gráfica (Eel)...")
    
    # =========================================================================
    # NOTA: Funções  foram convertidas passivamente pelo MockEel.
    # Na Fase 2, instalaremos o QWebChannel para restaurar o IO com JS.
    # =========================================================================

class VexyloWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VEXYLO DASHBOARD v1.0")
        self.resize(1280, 720)
        
        # FORÇAR O ÍCONE NATIVO NA BARRA DE TAREFAS
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, 'web', 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        # Configurar o Mini-Browser Embutido (Chromium)
        self.browser = QWebEngineView()
        
        # Permitir que a página local (file://) consiga carregar iframes remotos (http://)
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        
        # Configurar o QWebChannel antes de carregar a página
        self.channel = QWebChannel()
        self.bridge = VexyloBridge(self)
        self.channel.registerObject("backend", self.bridge)
        self.browser.page().setWebChannel(self.channel)

        # Mapear o caminho do index.html local de forma segura e absoluta
        index_path = os.path.join(current_dir, 'web', 'index.html')
        self.browser.setUrl(QUrl.fromLocalFile(index_path))
        
        self.setCentralWidget(self.browser)

        # Iniciar o Timer de Telemetria no Main Thread
        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self.update_telemetry)
        self.telemetry_timer.start(1000)

    def update_telemetry(self):
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
                print(f"[!] Erro na telemetria: {e}")

if __name__ == "__main__":
    print("[DEBUG] A iniciar QApplication...")
    app = QApplication(sys.argv)
    
    # Define o ícone global da aplicação
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, 'web', 'icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        
    print("[DEBUG] A instanciar VexyloWindow...")
    window = VexyloWindow()
    print("[DEBUG] A mostrar janela...")
    window.show()
    print("[DEBUG] A iniciar loop de eventos (app.exec())...")
    sys.exit(app.exec())
