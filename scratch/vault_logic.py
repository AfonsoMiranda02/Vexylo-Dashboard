import os
import shutil
import zipfile
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

def _derivar_chave(password: str) -> bytes:
    salt = b'vexylo_secret_salt_123'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def api_create_vexylo_vault(folder_path, password):
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

def api_mount_vexylo_vault(vault_path, password):
    if not os.path.isfile(vault_path) or not vault_path.endswith('.vexylo'):
        return {"success": False, "error": "Caminho não é um cofre Vexylo válido"}
    try:
        chave = _derivar_chave(password)
        f_suite = Fernet(chave)

        # 1. Read and decrypt
        with open(vault_path, 'rb') as f:
            encrypted_data = f.read()
        try:
            decrypted_data = f_suite.decrypt(encrypted_data)
        except Exception:
            return {"success": False, "error": "Password incorreta ou cofre corrompido."}

        # 2. Save decrypted to tmp zip
        tmp_zip = vault_path + ".tmp.zip"
        with open(tmp_zip, 'wb') as f:
            f.write(decrypted_data)

        # 3. Extract zip to hidden mount folder
        home_dir = os.path.expanduser("~")
        mounts_dir = os.path.join(home_dir, ".vexylo_mounts")
        os.makedirs(mounts_dir, exist_ok=True)
        
        folder_name = os.path.basename(vault_path).replace('.vexylo', '')
        mount_path = os.path.join(mounts_dir, folder_name)
        
        if os.path.exists(mount_path):
            shutil.rmtree(mount_path)
        os.makedirs(mount_path)

        with zipfile.ZipFile(tmp_zip, 'r') as zip_ref:
            zip_ref.extractall(mount_path)
        
        os.remove(tmp_zip)
        
        return {"success": True, "mount_path": mount_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

def api_unmount_vexylo_vault(mount_path, vault_path, password):
    if not os.path.exists(mount_path):
        return {"success": False, "error": "Cofre não está montado"}
    try:
        chave = _derivar_chave(password)
        f_suite = Fernet(chave)

        # 1. Zip the mount folder
        zip_path = mount_path + ".tmp.zip"
        shutil.make_archive(mount_path + ".tmp", 'zip', mount_path)

        # 2. Encrypt the zip
        with open(zip_path, 'rb') as f:
            raw_data = f.read()
        encrypted_data = f_suite.encrypt(raw_data)

        # 3. Save as .vexylo
        with open(vault_path, 'wb') as f:
            f.write(encrypted_data)

        # 4. Clean up
        os.remove(zip_path)
        shutil.rmtree(mount_path)

        return {"success": True, "vault_path": vault_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    os.makedirs("test_folder", exist_ok=True)
    with open("test_folder/test.txt", "w") as f:
        f.write("Hello World")
    
    print("Testing create...")
    res1 = api_create_vexylo_vault("test_folder", "mypassword")
    print(res1)
    
    print("Testing mount...")
    res2 = api_mount_vexylo_vault("test_folder.vexylo", "mypassword")
    print(res2)
    
    if res2["success"]:
        mount_path = res2["mount_path"]
        with open(os.path.join(mount_path, "test2.txt"), "w") as f:
            f.write("Hello again")
        
        print("Testing unmount...")
        res3 = api_unmount_vexylo_vault(mount_path, "test_folder.vexylo", "mypassword")
        print(res3)
