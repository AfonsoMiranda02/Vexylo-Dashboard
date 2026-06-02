Vexylo Vaults: Sistema Multi-Cofre e Gestão de Contas
Em vez de um cofre simples, vamos construir um Gestor de Cofres Vexylo estilo 1Password / VeraCrypt completo, incluindo um novo sistema de configuração inicial (First-Run Experience) para proteger a aplicação!

O fluxo de funcionamento detalhado fica estabelecido da seguinte forma:

1. Arranque da Aplicação (First Run & Boot)
Quando a aplicação Vexylo Dashboard arranca pela primeira vez, o utilizador passa por um processo de configuração inicial (OOBE - Out of Box Experience).

1.1. Passo 1: Criação de Conta da App (OOBE): O utilizador é recebido por um ecrã para criar a sua Conta de Aplicação Local (Username e Password). Estas serão as credenciais mestras para bloquear o HUD e para aceder aos cofres.
1.2. Passo 2: Configuração da API Key (OOBE): Após criar a conta, avança para um segundo ecrã. Aqui o utilizador pode colocar uma API Key já existente ou solicitar a criação/associação de uma nova para conetar ao Backend Docker.
1.2.1. Função Skip: Este passo tem um botão [ SKIP / SALTAR ]. Se o utilizador clicar, surge um aviso de sistema: "AVISO: A aplicação (Telemetria, Dossiers, etc) não funcionará como desejado sem uma API Key válida."
1.3. Arranques Normais (Login): Nas futuras vezes que abrir a aplicação, só lhe será pedido o Username e Password da Conta da App (criada no passo 1.1) para desbloquear e entrar no HUD.
2. Aceder à Secção de Cofres (Botão 🛡️)
O utilizador clica no ícone 🛡️ no cabeçalho do HUD.

2.1. Autenticação do Cofre: Por segurança extra, para aceder ao painel de gestão de cofres, é exigida novamente a password da Conta da App.
2.2. OobE do Vault (First Vault Creation): Se for a primeiríssima vez que o utilizador acede ao cofre (ou seja, se tiver 0 cofres), o sistema não mostra logo o painel. Em vez disso, obriga-o a criar o seu primeiro cofre (nome, password e/ou key file).
2.3. Acesso ao Vault Manager: Só após criar esse primeiro cofre (ou se já tiver criado um antes), o utilizador entra no painel central "Vexylo Vault Manager", onde consegue visualizar todos os seus cofres criados numa lista/grelha. Se no futuro o utilizador apagar todos os cofres que tem, o painel volta a abrir normalmente mas apenas mostra uma lista vazia, até ele decidir criar um novo.
3. Gestão e Criação de Cofres (Vault Manager)
Dentro do painel Vault Manager, o utilizador tem controlo total sobre os seus múltiplos cofres.

3.1. Criar um Novo Cofre:
O utilizador clica em "Novo Cofre".
Define as propriedades: Nome do Cofre, Tipo de Segurança (Só Password, Só Ficheiro .key, ou Ambos) e seleciona opcionalmente uma ou mais pastas/ficheiros iniciais para incluir. (Se não selecionar nada, cria o cofre vazio).
O sistema mostra uma Progress Bar (Barra de Progresso) de compressão/encriptação, e depois volta ao Vault Manager.
3.2. Montar (Abrir) um Cofre Existente:
O utilizador clica num cofre da lista e tenta abri-lo.
Insere a Password e/ou faz upload do ficheiro .key exigido por esse cofre específico.
O sistema mostra uma Progress Bar (Barra de Progresso) calculada dinamicamente.
Se outro cofre já estiver montado, o sistema avisa que "Apenas 1 cofre pode estar ativo" e impede a montagem.
Se sucesso, o cofre é montado e a pasta surge no Gestor de Ficheiros. O utilizador pode gerir, apagar ou adicionar ficheiros.
3.3. Trancar um Cofre:
No Vault Manager, o utilizador clica para "Lock Vault".
Surge uma Progress Bar (Barra de Progresso) enquanto as novas alterações são comprimidas e encriptadas em segurança no ficheiro original, apagando a pasta montada do disco.
4. O Menu de Contexto (Right-Click) e Lógica de Progress Bar
Estado Bloqueado: Se o utilizador tiver 0 vaults criados, a opção de clique direito (Hide (Vexylo Vault)) estará visível mas inativa/inclicável (disabled).
Fluxo de Envio para o Cofre:
O utilizador clica com o botão direito num ficheiro/pasta e escolhe Hide.
Surge um painel de confirmação: "Tem a certeza que quer mover para um cofre?"
Respondendo "Sim", é pedida a Password da Conta da App.
Após validação, surge a lista de todos os Vaults criados. O utilizador seleciona o Vault de destino.
Insere a Password / Ficheiro .key do Vault escolhido.
Inicia-se o processo de transferência com a Progress Bar Inteligente.
Matemática da Barra de Progresso (Smart Chunking Avançado)
Para que a experiência seja incrivelmente fluída, a barra de carregamento será calculada dinamicamente, garantindo sempre que: Desencriptação + Processamento de Ficheiros + Encriptação = 100%

A divisão do peso processual depende dos ficheiros:

Fase 1 (Desencriptação): O peso é calculado consoante o tamanho do Vault atual versus o que vai ser transferido, mas será sempre <= 25% (podendo ser um valor inferior, como 5% ou 10% se a operação o ditar).
Fase 2 (Transferência de Ficheiros): Recebe o restante peso da operação, sendo sempre >= 50% (pois a Fase 1 e 3 nunca ultrapassarão juntas os 50%).
À medida que o Python copia ficheiro a ficheiro para o Vault, calcula a percentagem relativa (Tamanho do ficheiro copiado / Tamanho Total a Processar * Peso_Atribuído_A_Fase_2) e atualiza a barra passo a passo (mostrando o nome do ficheiro e o progresso incremental). Ficheiros de 1GB darão saltos enormes, ficheiros KB darão saltos minúsculos de <1%.
Fase 3 (Encriptação): O peso final de voltar a comprimir/encriptar o Vault é também calculado dinamicamente, garantindo que perfaz os exatos 100%, sendo também sempre <= 25%.
Proposed Changes
1. Backend e Lógica Principal (desktop-app/main.py)
Gestão de Sessão Local: Guardar as hashes das credenciais criadas no passo 1.1 num local_account.json encriptado.
Processo OOBE: Funções para lidar com o First-Run (verificar se a conta existe, se a API Key já foi posta).
Gestão Multi-Cofre: Um registo em JSON (vaults_registry.json) que mapeia todos os cofres criados (Nome -> Caminho no Disco, Tipo de Proteção).
Progress Bars: Funções Eel para reportar eventos de progresso durante as fases pesadas da operação de I/O de zip/unzip.
2. Frontend HTML/JS (desktop-app/web/index.html & script.js)
Novo Fluxo de Arranque: Esconder o painel de API Key original e substituí-lo por 3 novos ecrãs (Login, Criar Conta, Inserir API Key).
Vault Manager UI: Um ecrã (talvez a sobrepor o centro do HUD ou a substituir temporariamente a secção ativa) com as estatísticas dos cofres e listas clicáveis.
UI Progress Bars: Implementar barras de loading em HTML puro/CSS para dar feedback claro ao utilizador quando o vault for criado/aberto/fechado.
User Review Required
TIP

A tua ideia do fluxo de "First Run" (OOBE) com os dois ecrãs (Conta + API) está espetacular e é padrão da indústria em apps de segurança! Está 100% de acordo com o que imaginaste? Não adicionei "Open Questions" desta vez porque o fluxo ficou cristalino. Dá a tua aprovação final e arranco logo com o código!