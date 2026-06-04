# Vexylo Dashboard Core (v1.0) 🦇

## 1. 🦇 VISÃO GERAL & ARQUITETURA
O Vexylo Dashboard é um Mini-SO tático local focado em maximizar a produtividade e a gestão do dia a dia. Operando de forma 100% offline, funciona como o derradeiro utilitário de controlo.

**Ecossistema Híbrido:**
O projeto divide-se numa arquitetura moderna e isolada:
- **Frontend Local:** Desenvolvido em tecnologias web e encapsulado (PyQt6/Eel), atua como a interface tática do utilizador. Comunica de forma assíncrona com o backend através de JSON/HTTP.
- **Backend em Docker:** Um ambiente estritamente isolado em containers que assegura a integridade do sistema. É composto por:
  - **FastAPI:** Motor lógico e API.
  - **PostgreSQL:** Base de dados robusta.
  - **Portainer & Docker Socket Proxy:** Gestão segura do ecossistema.

---

## 2. 🚀 QUICK START (GUIA RÁPIDO)

Para executar o sistema de forma limpa e profissional, siga estes passos:

### Passo 1: Configurar Variáveis de Ambiente
Na raiz do projeto, copie o ficheiro de exemplo `.env.example` e crie um ficheiro `.env` com as suas passwords reais. 
```bash
cp .env.example .env
```
*(Nota: O ficheiro `.env` está protegido pelo `.gitignore` e nunca será submetido para controlo de versão).*

### Passo 2: Subir a API Backend (Docker)
Certifique-se de que o Docker Desktop está a correr. Lance todos os serviços (Base de Dados, API na porta 7004, etc.) em modo detached:
```bash
docker compose up --build -d
```

### Passo 3: Lançar a Interface Desktop (PyQt6)
Com a API a correr no Docker, pode finalmente iniciar a interface gráfica PyQt6/Eel:
```bash
python desktop-app/main.py
```

---

## 3. 📴 REQUISITOS DO SISTEMA (Deteção Automática)
A espinha dorsal (API) do Vexylo Dashboard está programada para se adaptar autonomamente à máquina onde corre. No arranque, realiza uma triagem granular do Sistema Operativo:

- **Windows:** Detetado instantaneamente via chamadas ao sistema (compatível com execução em ambientes PowerShell/CMD). Mapeia ferramentas como Winget/Choco.
- **Linux (Agnóstico):** Se detetar kernel Linux, o sistema lê o ficheiro `/etc/os-release` para identificar a distribuição exata. Com esta informação, mapeia de forma transparente o Package Manager nativo da distro (pacman, apt, dnf, zypper, apk, etc.).
- **macOS:** Sistemas da Apple resultam num bloqueio fatal e imediato, abortando a aplicação com um log de erro.

## 4. 🌐 MAPA DE PORTAS (LOCALHOST)
Todos os serviços correm de forma isolada, mas estão mapeados localmente nas seguintes portas para fácil acesso e administração tática:

| Serviço | Descrição | URL de Acesso Local |
| :--- | :--- | :--- |
| **API Core** | Endpoints CRUD & Nomad System (FastAPI) | [http://localhost:2060](http://localhost:2060) |
| **Base de Dados** | Acesso direto ao PostgreSQL | `localhost:2050` |
| **pgAdmin** | Painel de controlo visual para gerir a BD | [http://localhost:2070](http://localhost:2070) |
| **Portainer** | Gestor visual isolado de containers Docker | [http://localhost:2080](http://localhost:2080) |

---

## ⚠️ IMPORTANT LICENSE NOTICE
Although GitHub may detect this project as a standard MIT license, it features an explicit **Non-Commercial Amendment (Commons Clause)** in the `LICENSE` file. Commercial use or profiting from this software is **strictly prohibited**.
