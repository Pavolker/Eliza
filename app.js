// ==========================================================================
// APP.JS — LÓGICA DE INTERACTION ELIZA 2026
// Conexão via WebSocket, Gerenciamento de Sessão e Efeitos Atmosféricos
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    const chatHistory = document.getElementById('chat-history');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const typingIndicator = document.getElementById('typing-indicator');
    const connectionDot = document.getElementById('connection-dot');
    const connectionText = document.getElementById('connection-text');
    
    // Elementos adicionais para Cards e Filtros
    const cardsContainer = document.getElementById('cards-container');
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    let socket = null;
    let currentResponseElement = null;
    let reconnectTimeout = null;
    let reconnectDelay = 1000; // Começa com 1s
    let shouldReconnect = true; // Controla se o cliente deve reconectar automaticamente

    // Estado local para os cards desbloqueados
    const activeCards = {};
    const foyerTotals = {
        interne: 8,
        externe: 5,
        strategique: 6
    };

    // Recupera ou cria um ID de conversa persistente para o usuário
    let conversationId = localStorage.getItem('eliza_session_id') || 'new';

    // Inicializa o tema padrão como Calm
    document.body.className = 'theme-calm';

    // Função de Conexão WebSocket com Reconexão Automática
    function connectWebSocket() {
        shouldReconnect = true;
        const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        const protocol = isLocalhost ? (window.location.protocol === 'https:' ? 'wss' : 'ws') : 'wss';
        const wsHost = isLocalhost ? window.location.host : 'eliza.mdh-hability.com';
        const wsUrl = `${protocol}://${wsHost}/ws/${conversationId}`;
        
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log('Conectado ao consultório da ELIZA.');
            connectionDot.className = 'connection-dot connected';
            connectionText.textContent = 'Em sintonia com você';
            reconnectDelay = 1000; // Reseta o delay
            if (reconnectTimeout) clearTimeout(reconnectTimeout);
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'status':
                    console.log('Status do servidor:', data.content);
                    break;
                    
                case 'typing':
                    if (data.content) {
                        showTypingIndicator();
                    } else {
                        hideTypingIndicator();
                    }
                    break;
                    
                case 'token':
                    // Oculta indicador de digitação no primeiro token
                    hideTypingIndicator();
                    appendToken(data.content);
                    break;
                    
                case 'emotion':
                    // Transita o fundo do aplicativo suavemente de acordo com a emoção
                    changeAtmosphere(data.content);
                    break;
                    
                case 'session_id':
                    // Sincroniza o ID persistente da conversa no cliente
                    if (conversationId !== data.content) {
                        conversationId = data.content;
                        localStorage.setItem('eliza_session_id', conversationId);
                        console.log('ID de conversa atualizado e persistido:', conversationId);
                    }
                    break;
                    
                case 'card_trigger':
                    // Processa e exibe o card dinamicamente no painel de temas
                    handleCardTrigger(data.content);
                    break;

                case 'end':
                    // Finaliza a resposta atual
                    currentResponseElement = null;
                    enableInput();
                    break;
                    
                case 'error':
                    hideTypingIndicator();
                    appendErrorMessage(data.content);
                    disableInput();
                    // Se for erro de concorrência ou desconexão forçada, impede reconexão
                    if (data.content.includes("outra aba") || data.content.includes("desconectada")) {
                        shouldReconnect = false;
                    }
                    break;
            }
        };

        socket.onclose = () => {
            console.log('Conexão fechada.');
            connectionDot.className = 'connection-dot disconnected';
            disableInput();
            
            if (shouldReconnect) {
                connectionText.textContent = 'Conexão instável, restabelecendo...';
                // Backoff exponencial para reconexão
                reconnectTimeout = setTimeout(() => {
                    reconnectDelay = Math.min(reconnectDelay * 2, 30000); // Máximo 30s
                    connectWebSocket();
                }, reconnectDelay);
            } else {
                connectionText.textContent = 'Sessão desconectada';
            }
        };

        socket.onerror = (error) => {
            console.error('Erro no WebSocket:', error);
            socket.close();
        };
    }

    // Gerenciamento dos Cards Dinâmicos (Seus Temas)
    function handleCardTrigger(cardData) {
        const cardId = cardData.id;
        
        // Se o card já existe, atualiza seu status se for o caso
        if (activeCards[cardId]) {
            const cardEl = document.querySelector(`.theme-card[data-id="${cardId}"]`);
            if (cardEl && cardData.status === 'novo') {
                activeCards[cardId].status = 'novo';
                cardEl.className = `theme-card type-${cardData.type} status-novo`;
                // Move para o topo
                cardsContainer.prepend(cardEl);
            }
            updatePlaceholderVisibility();
            return;
        }

        // Se for um novo card mapeado
        activeCards[cardId] = cardData;

        // Criar elemento DOM
        const cardDiv = document.createElement('div');
        cardDiv.className = `theme-card type-${cardData.type} status-${cardData.status}`;
        cardDiv.setAttribute('data-id', cardId);
        cardDiv.setAttribute('data-foyer', cardData.foyer);

        // Badge label em português
        let foyerLabel = '';
        if (cardData.foyer === 'interne') foyerLabel = 'Interno';
        else if (cardData.foyer === 'externe') foyerLabel = 'Externo';
        else if (cardData.foyer === 'strategique') foyerLabel = 'Estratégico';
        else if (cardData.foyer === 'connection') foyerLabel = 'Conexão';
        else if (cardData.foyer === 'saut') foyerLabel = 'Salto';
        else if (cardData.foyer === 'reflexao') foyerLabel = 'Reflexão';

        cardDiv.innerHTML = `
            <div class="card-header-row">
                <div class="card-icon">${cardData.icon || '📋'}</div>
                <div class="card-title">${cardData.title}</div>
                <span class="card-foyer-badge badge-${cardData.foyer}">${foyerLabel}</span>
            </div>
            <p class="card-text">${cardData.text}</p>
            <div class="card-details">
                <p>Mapeado durante nossa conversa. Este tema faz parte do seu processo de autoconhecimento ativo.</p>
                <div class="card-actions">
                    <button class="card-btn archive-btn">${cardData.status === 'arquivado' ? 'Restaurar' : 'Arquivar'}</button>
                    <button class="card-btn expand-close-btn">Fechar</button>
                </div>
            </div>
        `;

        // Event listener para expandir/recolher
        cardDiv.addEventListener('click', (e) => {
            if (e.target.classList.contains('card-btn')) return;
            
            // Fecha outros cards que estejam expandidos
            document.querySelectorAll('.theme-card.expanded').forEach(el => {
                if (el !== cardDiv) el.classList.remove('expanded');
            });
            
            cardDiv.classList.toggle('expanded');
            
            // Remove o brilho de novo ao interagir
            if (cardDiv.classList.contains('status-novo')) {
                cardDiv.classList.remove('status-novo');
                cardDiv.classList.add('status-ativo');
                activeCards[cardId].status = 'ativo';
            }
        });

        // Event listener para botão de arquivar
        const archiveBtn = cardDiv.querySelector('.archive-btn');
        archiveBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const currentStatus = activeCards[cardId].status;
            if (currentStatus === 'arquivado') {
                activeCards[cardId].status = 'ativo';
                cardDiv.classList.remove('status-arquivado');
                cardDiv.classList.add('status-ativo');
                archiveBtn.textContent = 'Arquivar';
            } else {
                activeCards[cardId].status = 'arquivado';
                cardDiv.classList.remove('status-novo', 'status-ativo');
                cardDiv.classList.add('status-arquivado');
                cardDiv.classList.remove('expanded');
                archiveBtn.textContent = 'Restaurar';
            }
            applyFilters();
        });

        // Event listener para botão Fechar
        const closeBtn = cardDiv.querySelector('.expand-close-btn');
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            cardDiv.classList.remove('expanded');
        });

        // Adiciona ao início do contêiner
        cardsContainer.prepend(cardDiv);
        
        // Atualiza UI
        updatePlaceholderVisibility();
        updateFoyerProgress();
        applyFilters();
    }

    function updatePlaceholderVisibility() {
        const placeholder = document.querySelector('.no-cards-placeholder');
        const hasCards = cardsContainer.querySelector('.theme-card') !== null;
        if (placeholder) {
            placeholder.style.display = hasCards ? 'none' : 'flex';
        }
    }

    function updateFoyerProgress() {
        const counts = { interne: 0, externe: 0, strategique: 0 };
        
        Object.values(activeCards).forEach(card => {
            if (counts[card.foyer] !== undefined) {
                counts[card.foyer]++;
            }
        });

        Object.keys(foyerTotals).forEach(f => {
            const unlocked = counts[f];
            const total = foyerTotals[f];
            const score = (unlocked / total) * 10;
            
            const scoreEl = document.getElementById(`foyer-score-${f}`);
            const barEl = document.getElementById(`foyer-bar-${f}`);
            
            if (scoreEl) scoreEl.textContent = score.toFixed(1);
            if (barEl) barEl.style.width = `${Math.min((unlocked / total) * 100, 100)}%`;
        });
    }

    function applyFilters() {
        const activeFilterBtn = document.querySelector('.filter-btn.active');
        if (!activeFilterBtn) return;
        
        const filter = activeFilterBtn.getAttribute('data-filter');
        const cards = cardsContainer.querySelectorAll('.theme-card');
        
        cards.forEach(card => {
            const cardFoyer = card.getAttribute('data-foyer');
            if (filter === 'all') {
                card.style.display = 'block';
            } else if (cardFoyer === filter) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    // Configuração dos Botões de Filtro
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            applyFilters();
        });
    });

    // Gerenciamento do Histórico de Mensagens
    function showTypingIndicator() {
        typingIndicator.classList.remove('hidden');
        scrollToBottom();
    }

    // Oculta indicador de digitação
    function hideTypingIndicator() {
        typingIndicator.classList.add('hidden');
    }

    function appendToken(token) {
        if (!currentResponseElement) {
            // Cria um novo contêiner de mensagem para a resposta da ELIZA
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message eliza-message';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            messageDiv.appendChild(contentDiv);
            
            chatHistory.appendChild(messageDiv);
            currentResponseElement = contentDiv;
        }
        
        // Adiciona o token ao conteúdo da mensagem
        currentResponseElement.innerHTML += token;
        scrollToBottom();
    }

    function appendUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;
        
        messageDiv.appendChild(contentDiv);
        chatHistory.appendChild(messageDiv);
        scrollToBottom();
    }

    function appendErrorMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message eliza-message system-error';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.style.color = '#ff8787';
        contentDiv.textContent = text;
        
        messageDiv.appendChild(contentDiv);
        chatHistory.appendChild(messageDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // Desativa input de chat
    function disableInput() {
        userInput.disabled = true;
        userInput.placeholder = "Aguardando sintonia...";
    }

    // Ativa input de chat
    function enableInput() {
        userInput.disabled = false;
        userInput.placeholder = "Fale comigo, estou ouvindo...";
        userInput.focus();
    }

    // Mudança suave na iluminação ambiental baseada na emoção
    function changeAtmosphere(emotion) {
        const validEmotions = ['calm', 'joy', 'sadness', 'anger', 'anxiety'];
        if (validEmotions.includes(emotion)) {
            // Remove temas anteriores e adiciona o novo
            validEmotions.forEach(e => document.body.classList.remove(`theme-${e}`));
            document.body.classList.add(`theme-${emotion}`);
            console.log(`Atmosfera alterada para: ${emotion}`);
        }
    }

    // Submissão do Formulário de Envio
    chatForm.addEventListener('submit', (event) => {
        event.preventDefault();
        
        const text = userInput.value.trim();
        if (!text || socket.readyState !== WebSocket.OPEN) return;

        // Adiciona a mensagem do usuário na tela
        appendUserMessage(text);
        
        // Envia para o backend via WebSocket
        socket.send(text);
        
        // Limpa o campo e desativa input temporariamente até a ELIZA responder
        userInput.value = '';
        disableInput();
        showTypingIndicator();
    });

    // Reinicia a conversa de forma limpa ao clicar no botão de reset
    const resetButton = document.getElementById('reset-button');
    if (resetButton) {
        resetButton.addEventListener('click', () => {
            if (confirm('Deseja reiniciar a conversa e limpar o histórico?')) {
                localStorage.removeItem('eliza_session_id');
                conversationId = 'new';
                
                // Limpa o feed visual de mensagens
                chatHistory.innerHTML = `
                    <div class="message eliza-message initial-message">
                        <div class="message-content">
                            Olá. Estou aqui e pronta para ouvir você. Como você está se sentindo hoje?
                        </div>
                    </div>
                `;

                // Limpa o painel de cards e estados
                cardsContainer.querySelectorAll('.theme-card').forEach(el => el.remove());
                for (const key in activeCards) {
                    delete activeCards[key];
                }
                updatePlaceholderVisibility();
                updateFoyerProgress();
                
                // Força reconexão WebSocket enviando 'new' para o servidor
                if (socket) {
                    socket.close();
                }
            }
        });
    }

    // Inicia conexão
    connectWebSocket();
});
