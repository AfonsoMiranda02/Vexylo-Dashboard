# 🛡️ COFRE DE CREDENCIAIS - VEXYLO SOFTWARE (VEXYLO DASHBOARD)

Este documento contém a listagem completa de todas as chaves, passwords e tokens configurados para o funcionamento de todo o ecossistema (Frontend, Backend, Docker e Base de Dados).

---

## 1. 🔐 Ecrã de Bloqueio UI (Vexylo Dashboard)
O portal de entrada principal da aplicação desktop que bloqueia o HUD.
- **Tipo:** System API Key (Master)
- **Chave Atual:** `4053cbd5-0eab-46c5-9d0a-9c1a49e4f0ab`
- **Ficheiro de Origem:** `desktop-app/main.py` (método `api_verificar_api_key`)

---

## 2. 🐳 Docker Backend API (Porta 2060)
A API FastApi local que comunica com a base de dados e fornece telemetria avançada/dossiers.
- **Username:** `batman`
- **Password:** `supersecretpassword`
- **Autenticação:** Cookie-based (`session_token`)
- **Ficheiro de Origem Frontal:** `desktop-app/main.py` (`API_USER` e `API_PASS`)
- **Ficheiro de Origem Servidor:** `api-server/security.py` ou `.env` do Docker

---

## 3. 🗄️ Base de Dados PostgreSQL (Porta 5432 / Docker DB)
A base de dados estrutural do sistema onde habitam os perfis e dossiers.
- **Host:** `db` (Interno no Docker) / `localhost` (Externo)
- **Porta:** `5432`
- **Database:** `superdashboard`
- **User:** `postgres`
- **Password:** `supersecretpassword`
- **Ficheiro de Origem:** `api-server/database.py` e `docker-compose.yml`

---

## 4. 🗃️ Cofre Criptográfico Virtual (Vault.bin)
O cofre isolado implementado no Gestor de Ficheiros.
- **Master Password:** (Definida por ti no primeiro momento em que montaste o cofre)
- Se ainda não criaste nada no cofre criptográfico, a password será aquela que definires na primeira vez que o tentares montar no HUD.
