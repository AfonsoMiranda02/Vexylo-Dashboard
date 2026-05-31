# BatComputer Core (v1.0) 🦇

## 1. 🦇 VISÃO GERAL & ARQUITETURA
O BatComputer é um Mini-SO tático local focado em maximizar a produtividade e a gestão do dia a dia. Operando de forma 100% offline, funciona como o derradeiro utilitário de controlo.

**Ecossistema Híbrido:**
O projeto divide-se numa arquitetura moderna e isolada:
- **Frontend Local:** Desenvolvido em tecnologias web e encapsulado (ex: via Eel/Python), atua como a interface tática do utilizador. Comunica de forma assíncrona com o backend através de JSON/HTTP.
- **Backend em Docker:** Um ambiente estritamente isolado em containers que assegura a integridade do sistema. É composto por:
  - **FastAPI:** Motor lógico e API residente na porta 2060.
  - **PostgreSQL:** Base de dados robusta na porta 2050 (internamente 5432).
  - **Portainer & Docker Socket Proxy:** Gestão segura do ecossistema na porta 2080. O acesso ao socket do Docker é filtrado e protegido pelo proxy para garantir que apenas os serviços com a label do projeto têm permissões.

## 2. 📴 REQUISITOS DO SISTEMA (Deteção Automática)
A espinha dorsal (API) do BatComputer está programada para se adaptar autonomamente à máquina onde corre. No arranque, realiza uma triagem granular do Sistema Operativo:

- **Windows:** Detetado instantaneamente via chamadas ao sistema (compatível com execução em ambientes PowerShell/CMD). Mapeia ferramentas como Winget/Choco.
- **Linux (Agnóstico):** Se detetar kernel Linux, o sistema lê o ficheiro `/etc/os-release` para identificar a distribuição exata. Com esta informação, mapeia de forma transparente o Package Manager nativo da distro (pacman, apt, dnf, zypper, apk, etc.).
- **macOS:** Sistemas da Apple resultam num bloqueio fatal e imediato, abortando a aplicação com um log de erro.

## 3. 🚀 GUIA DE EXECUÇÃO: WINDOWS
**Pré-requisitos:**
- Docker Desktop instalado e em execução (configurado com backend WSL2).
- XAMPP ou outro ambiente de desenvolvimento (opcional para o frontend web, dependendo do setup).

**Instruções (PowerShell):**
No PowerShell, o operador `&&` não é suportado de forma nativa como no Bash clássico (a menos que se use PowerShell 7+). Para garantir compatibilidade absoluta, utilize os comandos com `;` ou execute-os separadamente:

*Parar serviços e limpar:*
```powershell
docker compose down
```

*Compilar e levantar serviços:*
```powershell
docker compose up --build -d
```

> **Dica de Automação:** Nas definições do Docker Desktop (Settings > General), ative a opção "Start Docker Desktop when you log in" para que o ecossistema base esteja sempre pronto quando ligar o computador.

## 4. 🦅 GUIA DE EXECUÇÃO: LINUX (Mapeamento de Distros)
**Pré-requisitos:**
- Ter o Docker e o plugin docker-compose instalados.
- Garantir que o serviço do Docker arranca com o sistema através do systemd:
```bash
sudo systemctl enable --now docker
```

**Instruções (Bash):**
No terminal do Linux (Bash/Zsh), pode agrupar os processos num único pipeline limpo com `&&`:
```bash
docker compose down && docker compose up --build -d
```

**Tabela de Equivalência de Comandos (Utility Belt):**
O BatComputer adapta dinamicamente as suas rotinas internas (via `/api/nomad/os`) consoante a arquitetura detetada:

| Família de Distros | Distribuições Comuns | Comando de Instalação | Comando de Remoção |
| :--- | :--- | :--- | :--- |
| **Arch-based** | Arch, Manjaro, Endeavour | `pacman -S` | `pacman -R` |
| **Debian-based** | Ubuntu, Mint, Debian | `apt install` | `apt remove` |
| **Fedora/RHEL** | Fedora, CentOS, Rocky | `dnf install` | `dnf remove` |
| **SUSE-based** | openSUSE, SLES | `zypper in` | `zypper rm` |
| **Alpine** | Alpine Linux | `apk add` | `apk del` |

## 5. 🌐 MAPA DE PORTAS (LOCALHOST)
Todos os serviços correm de forma isolada, mas estão mapeados localmente nas seguintes portas para fácil acesso e administração tática:

| Serviço | Descrição | URL de Acesso Local |
| :--- | :--- | :--- |
| **API Core** | Endpoints CRUD & Nomad System (FastAPI) | [http://localhost:2060](http://localhost:2060) |
| **Base de Dados** | Acesso direto ao PostgreSQL | `localhost:2050` |
| **pgAdmin** | Painel de controlo visual para gerir a BD | [http://localhost:2070](http://localhost:2070) |
| **Portainer** | Gestor visual isolado de containers Docker | [http://localhost:2080](http://localhost:2080) |

*(Nota: O Docker Socket Proxy garante que o Portainer comunica em segurança localmente; lembre-se da flag `--no-tls` se necessário, embora por defeito a ligação TCP já esteja configurada sem TLS no nosso ficheiro compose).*
